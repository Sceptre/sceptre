"""
Integration tests for max_concurrency feature
"""

from unittest.mock import Mock, patch, MagicMock

from sceptre.context import SceptreContext
from sceptre.plan.plan import SceptrePlan
from sceptre.plan.executor import SceptrePlanExecutor
from sceptre.stack import Stack


class TestMaxConcurrencyIntegration:
    """Integration tests for max_concurrency feature across the stack"""

    def setup_method(self, method):
        # Create mock stacks
        self.stack1 = Mock(spec=Stack)
        self.stack1.name = "stack1"
        self.stack2 = Mock(spec=Stack)
        self.stack2.name = "stack2"
        self.stack3 = Mock(spec=Stack)
        self.stack3.name = "stack3"

    def test_context_to_plan_to_executor_flow(self):
        """Test that max_concurrency flows correctly from context to plan to executor"""
        # Create context with max_concurrency
        context = SceptreContext(
            project_path="/fake/path", command_path="test-stack", max_concurrency=2
        )

        # Mock the config reader and stack graph
        with patch("sceptre.plan.plan.ConfigReader") as mock_config_reader, patch(
            "sceptre.plan.plan.StackGraph"
        ) as mock_stack_graph:

            mock_config_reader_instance = Mock()
            mock_config_reader.return_value = mock_config_reader_instance
            mock_config_reader_instance.construct_stacks.return_value = (
                [self.stack1, self.stack2, self.stack3],
                [self.stack1, self.stack2, self.stack3],
            )

            mock_stack_graph_instance = Mock()
            mock_stack_graph.return_value = mock_stack_graph_instance

            # Create plan
            plan = SceptrePlan(context)

            # Verify max_concurrency is stored in plan
            assert plan.max_concurrency == 2

    def test_executor_receives_max_concurrency_from_plan(self):
        """Test that SceptrePlanExecutor receives max_concurrency from plan"""
        launch_order = [{self.stack1, self.stack2, self.stack3}]  # 3 stacks in parallel
        max_concurrency = 2

        executor = SceptrePlanExecutor("launch", launch_order, max_concurrency)

        # Verify executor limits threads correctly
        assert executor.num_threads == 2

    @patch("sceptre.plan.executor.ThreadPoolExecutor")
    def test_end_to_end_concurrency_limiting(self, mock_thread_pool):
        """Test end-to-end concurrency limiting from context to ThreadPoolExecutor"""
        # Setup context with max_concurrency
        context = SceptreContext(
            project_path="/fake/path", command_path="test-stack", max_concurrency=1
        )

        # Mock the config reader and dependencies
        with patch("sceptre.plan.plan.ConfigReader") as mock_config_reader, patch(
            "sceptre.plan.plan.StackGraph"
        ) as mock_stack_graph:

            mock_config_reader_instance = Mock()
            mock_config_reader.return_value = mock_config_reader_instance
            mock_config_reader_instance.construct_stacks.return_value = (
                [self.stack1, self.stack2, self.stack3],
                [self.stack1, self.stack2, self.stack3],
            )

            mock_stack_graph_instance = Mock()
            mock_stack_graph.return_value = mock_stack_graph_instance

            # Mock ThreadPoolExecutor
            mock_executor_instance = MagicMock()
            mock_thread_pool.return_value.__enter__.return_value = (
                mock_executor_instance
            )
            mock_thread_pool.return_value.__exit__.return_value = None

            # Mock futures
            mock_future = MagicMock()
            mock_future.result.return_value = (self.stack1, "SUCCESS")
            mock_executor_instance.submit.return_value = mock_future

            # Create and execute plan
            plan = SceptrePlan(context)
            plan.command = "launch"
            plan.launch_order = [{self.stack1, self.stack2, self.stack3}]

            with patch(
                "sceptre.plan.executor.as_completed", return_value=[mock_future] * 3
            ):
                plan._execute()

            # Verify ThreadPoolExecutor was created with max_workers=1 (our max_concurrency)
            mock_thread_pool.assert_called_once_with(max_workers=1)

    def test_no_max_concurrency_uses_natural_limit(self):
        """Test that when max_concurrency is None, natural concurrency is used"""
        context = SceptreContext(
            project_path="/fake/path",
            command_path="test-stack",
            # max_concurrency=None (default)
        )

        launch_order = [{self.stack1, self.stack2, self.stack3}]  # 3 stacks in parallel

        executor = SceptrePlanExecutor("launch", launch_order, context.max_concurrency)

        # Should use natural concurrency (3 stacks)
        assert executor.num_threads == 3

    def test_max_concurrency_larger_than_needed(self):
        """Test that max_concurrency larger than needed uses natural limit"""
        context = SceptreContext(
            project_path="/fake/path",
            command_path="test-stack",
            max_concurrency=10,  # Much larger than our 2 stacks
        )

        launch_order = [{self.stack1, self.stack2}]  # Only 2 stacks in parallel

        executor = SceptrePlanExecutor("launch", launch_order, context.max_concurrency)

        # Should use natural concurrency (2 stacks) instead of max_concurrency (10)
        assert executor.num_threads == 2

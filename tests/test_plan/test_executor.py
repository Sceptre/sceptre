from unittest.mock import Mock, patch, MagicMock

from sceptre.plan.executor import SceptrePlanExecutor
from sceptre.stack import Stack


class TestSceptrePlanExecutor:
    def setup_method(self, method):
        # Create mock stacks
        self.stack1 = Mock(spec=Stack)
        self.stack1.name = "stack1"
        self.stack2 = Mock(spec=Stack)
        self.stack2.name = "stack2"
        self.stack3 = Mock(spec=Stack)
        self.stack3.name = "stack3"

        # Common test data
        self.command = "launch"

    def test_max_concurrency_none_uses_natural_limit(self):
        """Test that when max_concurrency is None, natural concurrency is used"""
        launch_order = [{self.stack1, self.stack2, self.stack3}]  # 3 stacks in parallel

        executor = SceptrePlanExecutor(self.command, launch_order, max_concurrency=None)

        assert executor.num_threads == 3

    def test_max_concurrency_limits_threads(self):
        """Test that max_concurrency limits the number of threads"""
        launch_order = [{self.stack1, self.stack2, self.stack3}]  # 3 stacks in parallel

        executor = SceptrePlanExecutor(self.command, launch_order, max_concurrency=2)

        assert executor.num_threads == 2

    def test_max_concurrency_larger_than_batch_size_uses_natural_limit(self):
        """Test that max_concurrency larger than batch size uses natural limit"""
        launch_order = [{self.stack1, self.stack2}]  # 2 stacks in parallel

        executor = SceptrePlanExecutor(self.command, launch_order, max_concurrency=5)

        assert executor.num_threads == 2

    def test_max_concurrency_one_sequential_execution(self):
        """Test that max_concurrency=1 forces sequential execution"""
        launch_order = [{self.stack1, self.stack2, self.stack3}]  # 3 stacks in parallel

        executor = SceptrePlanExecutor(self.command, launch_order, max_concurrency=1)

        assert executor.num_threads == 1

    def test_empty_launch_order_uses_one_thread(self):
        """Test that empty launch order defaults to 1 thread"""
        launch_order = [set()]  # Empty batch

        executor = SceptrePlanExecutor(self.command, launch_order, max_concurrency=None)

        assert executor.num_threads == 1

    def test_empty_launch_order_with_max_concurrency(self):
        """Test that empty launch order with max_concurrency still defaults to 1 thread"""
        launch_order = [set()]  # Empty batch

        executor = SceptrePlanExecutor(self.command, launch_order, max_concurrency=5)

        assert executor.num_threads == 1

    def test_multiple_batches_uses_largest_batch_size(self):
        """Test that thread count is based on the largest batch"""
        launch_order = [
            {self.stack1},  # 1 stack
            {self.stack2, self.stack3},  # 2 stacks (largest batch)
        ]

        executor = SceptrePlanExecutor(self.command, launch_order, max_concurrency=None)

        assert executor.num_threads == 2

    def test_multiple_batches_with_max_concurrency(self):
        """Test max_concurrency applies to largest batch across multiple batches"""
        launch_order = [
            {self.stack1},  # 1 stack
            {self.stack2, self.stack3},  # 2 stacks (largest batch)
        ]

        executor = SceptrePlanExecutor(self.command, launch_order, max_concurrency=1)

        assert executor.num_threads == 1

    @patch("sceptre.plan.executor.ThreadPoolExecutor")
    def test_execute_uses_correct_max_workers(self, mock_thread_pool):
        """Test that execute() uses the calculated num_threads as max_workers"""
        launch_order = [{self.stack1, self.stack2}]
        max_concurrency = 1

        # Mock the context manager and its methods
        mock_executor_instance = MagicMock()
        mock_thread_pool.return_value.__enter__.return_value = mock_executor_instance
        mock_thread_pool.return_value.__exit__.return_value = None

        # Mock submit to return a future-like object
        mock_future = MagicMock()
        mock_future.result.return_value = (self.stack1, "SUCCESS")
        mock_executor_instance.submit.return_value = mock_future

        # Mock as_completed to return the futures
        with patch(
            "sceptre.plan.executor.as_completed",
            return_value=[mock_future, mock_future],
        ):
            executor = SceptrePlanExecutor(self.command, launch_order, max_concurrency)
            executor.execute()

        # Verify ThreadPoolExecutor was called with correct max_workers
        mock_thread_pool.assert_called_once_with(max_workers=1)

    def test_zero_max_concurrency_treated_as_none(self):
        """Test that max_concurrency=0 is treated as no limit (natural concurrency)"""
        launch_order = [{self.stack1, self.stack2, self.stack3}]  # 3 stacks in parallel

        executor = SceptrePlanExecutor(self.command, launch_order, max_concurrency=0)

        # Should use natural concurrency (3) since 0 is treated as "no limit"
        assert executor.num_threads == 3

    def test_negative_max_concurrency_treated_as_none(self):
        """Test that negative max_concurrency is treated as no limit (natural concurrency)"""
        launch_order = [{self.stack1, self.stack2, self.stack3}]  # 3 stacks in parallel

        executor = SceptrePlanExecutor(self.command, launch_order, max_concurrency=-1)

        # Should use natural concurrency (3) since negative is treated as "no limit"
        assert executor.num_threads == 3

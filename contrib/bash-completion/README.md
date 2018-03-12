# bash completion script

This script will provide basic bash completion for `sceptre` commands and options.

## installation

If you're already using bash completion scripts, copy the `sceptre` file to the relevant folder.

Otherwise, just copy it to e.g. your home directory:

```shell
mv sceptre ~/.sceptre.completion
```
and add a line to your `bashrc` to source it whenever you start a new interactive shell:

```shell
[[ -f ~/.sceptre.completion ]] && source ~/.sceptre.completion
```

## limitations
This script will not handle all possibilities (e.g. two options in the same command) and relies on the recommended project structure:

```shell
├── config
│   ├── config.yaml
│   ├── production
│   │   ├── configA.yaml
│   │   ├── ...
│   │   └── configX.yaml
│   └── staging
│       ├── configY.yaml
│       └── ...
└── templates
    ├── tpl1.json
    └── ...
```

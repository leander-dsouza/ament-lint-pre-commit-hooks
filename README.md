[![build status](https://github.com/leander-dsouza/ament-lint-pre-commit-hooks/actions/workflows/lint.yml/badge.svg)](https://github.com/leander-dsouza/ament-lint-pre-commit-hooks/actions/workflows/lint.yml)

# ament-lint-pre-commit-hooks
Pre-commit hooks for [ament_lint](https://github.com/ament/ament_lint/tree/rolling). No ROS installation required.

### Using ament-lint-pre-commit-hooks with pre-commit

Add this to your `.pre-commit-config.yaml`

```yaml
-   repo: https://github.com/leander-dsouza/ament-lint-pre-commit-hooks.git
    rev: v1.0.0
    hooks:
    -   id: ament_cpplint
    -   id: ament_flake8
    -   id: ament_lint_cmake
    -   id: ament_mypy
    -   id: ament_pep257
    -   id: ament_uncrustify
    -   id: ament_xmllint
```
### Hooks available

* **`ament_cpplint`**

   Check code against the Google style conventions using cpplint as mentioned in [ament_cpplint](https://github.com/ament/ament_lint/tree/rolling/ament_cpplint) package.

   - `--filters FILTER,FILTER,...`

       A comma separated list of category filters to apply (`default: None`)

   - `--linelength N`

      The maximum line length (`default: 100`)

   - `--root ROOT`

      The --root option for cpplint (`default: None`)

   - `--exclude [EXCLUDE ...]`

      Exclude C/C++ files from being checked. (`default: []`)

   - `--output OUTPUT`

      The --output option for cpplint (`default: None`)

   - `--xunit-file XUNIT_FILE`

      Generate a xunit compliant XML file (`default: None`)

* **`ament_flake8`**

   Check code using flake8 as mentioned in the [ament_flake8](https://github.com/ament/ament_lint/tree/rolling/ament_flake8) package.

   - `--config path`

      The config file (`default: /installed_path/ament-lint-pre-commit-hooks/ament_lint_pre_commit_hooks/config/ament_flake8.ini`)

   - `--linelength N`

      The maximum line length (`default: specified in the config file`) (`default: None`)

   - `--exclude [filename ...]`

      The filenames to exclude. (`default: None`)

   - `--xunit-file XUNIT_FILE`

      Generate a xunit compliant XML file (`default: None`)

*  **`ament_lint_cmake`**

   Check CMake code against the style conventions as mentioned in the [ament_lint_cmake](https://github.com/ament/ament_lint/tree/rolling/ament_lint_cmake) package.

   - `--filters FILTERS`

      Filters for lint_cmake, for a list of filters see [here](https://github.com/richq/cmake-lint/blob/master/README.md#usage). (`default: `)

   - `--linelength N`

      The maximum line length (`default: 140`)

   - `--xunit-file XUNIT_FILE`

      Generate a xunit compliant XML file (`default: None`)

* **`ament_mypy`**

   Check code using mypy as mentioned in the [ament_mypy](https://github.com/ament/ament_lint/tree/rolling/ament_mypy) package.

    - `--config path`

        The config file (`default: /relative_path/ament-lint-pre-commit-hooks/ament_lint_pre_commit_hooks/config/ament_mypy.ini`)

    - `--exclude [filename ...]`

        The filenames to exclude. (`default: None`)

    - `--xunit-file XUNIT_FILE`

        Generate a xunit compliant XML file (`default: None`)

* **`ament_pep257`**

   Check docstrings against the style conventions in PEP 257 as mentioned in the [ament_pep257](https://github.com/ament/ament_lint/tree/rolling/ament_pep257) package.

    - `--ignore IGNORE [IGNORE ...]`

        Choose the list of error codes for pydocstyle NOT to check for. (`default: []`)

    - `--select SELECT [SELECT ...]`

        Choose the basic list of error codes for pydocstyle to check for. (`default: []`)

    - `--convention {google,pep257,numpy,ament}`

        Choose a preset list of error codes. Valid options are {`google`, `pep257`, `numpy`, `ament`}.

        The "ament" convention is defined as --ignore [`D100`, `D101`, `D102`, `D103`, `D104`, `D105`, `D106`,
        `D107`, `D203`, `D212`, `D404`]. (`default: ament`)

    - `--add-ignore ADD_IGNORE [ADD_IGNORE ...]`

        Ignore an extra error code, removing it from the list set by --(select/ignore) (`default: []`)

    - `--add-select ADD_SELECT [ADD_SELECT ...]`

        Check an extra error code, adding it to the list set by --(select/ignore). (`default: []`)

    - `--exclude [filename ...]`

        The filenames to exclude. (`default: []`)

    - `--xunit-file XUNIT_FILE`

        Generate a xunit compliant XML file (`default: None`)

* **`ament_uncrustify`**

   Check code style using uncrustify as mentioned in [ament_uncrustify](https://github.com/ament/ament_lint/tree/rolling/ament_uncrustify) package.

    - `--config CFG`

        The path to the uncrustify config file (`default: /relative_path/ament-lint-pre-commit-hooks/ament_lint_pre_commit_hooks/config/ament_uncrustify.cfg`)

    - `--linelength N`

        The maximum line length (`default: specified in the config file`) (`default: None`)

    - `--exclude [filename ...]`

        Exclude specific file names from the check. (`default: []`)

    - `--language {C,C++,CPP}`

        Passed to uncrustify as `-l <language>` to force a specific language rather then choosing one based on file extension (`default: None`)

    - `--reformat`
        Reformat the files in place (`default: False`)

    - `--xunit-file XUNIT_FILE`

        Generate a xunit compliant XML file (`default: None`)

* **`ament_xmllint`**

   Check XML markup using xmllint as mentioned in the [ament_xmllint](https://github.com/ament/ament_lint/tree/rolling/ament_xmllint) package.

    - `--exclude [filename ...]`

        Exclude specific file names and directory names from the check (`default: []`)

    - `--extensions [EXTENSIONS ...]`

        The file extensions of the files to check (`default: ['xml']`)

    - `--xunit-file XUNIT_FILE`

        Generate a xunit compliant XML file (`default: None`)

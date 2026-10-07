# digital-media-analysis

# Setup

0. Ensure you have all pre-requisites installed:
    - [uv](https://docs.astral.sh/uv/getting-started/installation/#installation-methods) – dependency & Python management
    - [make](https://www.gnu.org/software/make/) – meta-build system
    - [git](https://git-scm.com/install/) – version control system

1. Clone the repository.
    
    ```bash
    git clone git@github.com:igor-sosnowicz/digital-media-analysis.git
    ```


2. Install the dependencies.

    ```bash
    uv sync
    ```

3. Run the pipeline.

    ```bash
    make pipeline
    ```

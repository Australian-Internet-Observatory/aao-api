# Australian Ad Observatory API

This is the codebase for the Australian Ad Observatory API, which is a Mono-Lambda serverless application that provides an API for the [Australian Ad Observatory dashboard](https://github.com/ADMSCentre/australian-ad-observatory-dashboard-v2).

This also hosts the [documentation](https://admscentre.github.io/australian-ad-observatory-api) of the Australian Ad Observatory API.

## Dependencies

- Docker

> [!TIP]
>
> For Linux, install Docker using the following command (preferably from `~`):
>
> Update the package database:
>
> ```bash
> # Add Docker's official GPG key:
> sudo apt-get update
> sudo apt-get install ca-certificates curl
> sudo install -m 0755 -d /etc/apt/keyrings
> sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
> sudo chmod a+r /etc/apt/keyrings/docker.asc
> 
> # Add the repository to Apt sources:
> echo \
>   "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
>   $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}") stable" | \
>   sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
> sudo apt-get update
> ```
>
> Install the latest version of Docker:
>
> ```bash
> sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
> ```
>
> Verify the installation:
> 
> ```bash
> docker --version
> ```

## Setup

1. Create a `config.ini` file in the root directory of the project to store the AWS credentials and other settings. An example `sample_config.ini` is provided for reference.

2. Use [AWS SAM CLI](https://github.com/aws/aws-sam-cli) to run the API locally.

    2.1. Install AWS SAM CLI for your OS by following the [installation instructions](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html#install-sam-cli-instructions).

    > [!TIP] 
    >
    > For Linux, you can use the following command to install AWS SAM CLI (preferably from `~`):
    >
    > ```bash
    > curl -L https://github.com/aws/aws-sam-cli/releases/latest/download/aws-sam-cli-linux-x86_64.zip -o aws-sam-cli-linux-x86_64.zip
    > unzip aws-sam-cli-linux-x86_64.zip -d sam-installation
    > sudo ./sam-installation/install
    > sam --version
    > ```

    2.2 Run the following command to build the API:

    ```bash
    sudo sam build --use-container
    ```

    2.3 Run the following command to start the API locally:

    ```bash
    sudo sam local start-api
    ```

    2.4 The API will be available at `http://localhost:3000/`. To test it is working, try accessing the `/hello` endpoint:

    ```shell
    curl http://localhost:3000/hello
    # {"message": "Hello, world!"}
    ```

    2.5 To watch for changes in the source code and automatically rebuild the API, you can use the following command. You may first need to install `entr` using your package manager (e.g., `brew install entr` for MacOS or `sudo apt-get install entr` for Linux):

    ```bash
    find . -not -path "./.*" | entr -r sh -c 'sudo sam build --use-container && sudo sam local start-api'
    ```

3. **Alternatively**, you can run the API locally using Python in a virtual environment.

    3.1 For MacOS and Linux:

    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    ```

    3.2 For Windows:

    ```powershell   
    python -m venv .venv
    .\.venv\Scripts\activate
    pip install -r requirements.txt
    ```

## Testing

They can be run using the [`pytest`](https://docs.pytest.org/en/stable/) module, which you can install with:

```bash
pip install pytest
```

> [!NOTE]
>
> This dependency is not included in the `requirements.txt` file as it is only needed for testing purposes and not for the Lambda deployment.

To run the tests, you can use the following command from the root directory of the project:

```bash
python -m pytest test_directory_or_file
```

Where `test_directory_or_file` can be either a specific test file (e.g., `unittests/test_file.py`) or a directory containing tests (e.g., `unittests` or `apitests`).

> [!IMPORTANT]
>
> We are using the `python -m` command to run `pytest` instead of `pytest` directly to ensure that the correct Python interpreter is used, especially when working with virtual environments.
>
> Without this, you may encounter issues with the Python version or when importing modules such as `lambda_function`.

### Unit Tests

These tests target the individual components of the API (and not the endpoints). They are located in the `unittests` directory.

To run a specific test file:

```bash
python -m pytest unittests/test_file.py
```

To run all unit tests:

```bash
python -m pytest unittests
```

### API Tests

These tests target the API endpoints and are located in the `apitests` directory.

> [!IMPORTANT]
>
> The API tests are integration tests that target many protected endpoints and
> will require valid authentication credentials to run successfully. you will 
> need to set up the `config.ini` file with a valid `USERNAME` and `PASSWORD` 
> of actual accounts to run these tests successfully.

To run a specific test file:

```bash
python -m pytest apitests/test_file.py
```

To run all API tests:

```bash
python -m pytest apitests
```

## Deployment

To deploy the AWS Lambda function, follow these steps:

**For Linux and MacOS**

```shell
./scripts/package.sh
python3 -m scripts.deploy
python3 -m scripts.pulse
```

**For Windows**

```shell
./scripts/package.ps1
python -m scripts.deploy
python -m scripts.pulse
```

1. **Create the deployment package**:
   
From the root directory, run the `package.ps1` script to create the deployment package. This script will create a ZIP file containing the code and dependencies.

```powershell
./scripts/package.ps1
```

2. **Deploy the package to AWS Lambda**:
   
From the root directory, run the `deploy.py` script to upload the deployment package to AWS Lambda. Ensure that your `config.ini` file contains the correct AWS credentials and settings.

```bash
python -m scripts.deploy
```

This will update the Lambda function with the new code and dependencies.

3. **Test the deployment**:

The `pulse.py` script can be used to test the deployment. This script will invoke the `/hello` endpoint of the API and print the response.

```bash
python -m scripts.pulse
```

## Generate the API documentation

To generate the API documentation locally, you will need to run the following command in the root directory of the project:

```bash
python -m scripts.docgen
```

This will create a `swagger.yaml` OpenAPI Spec file in the root directory of the project, which describes the API and is compatible with Swagger UI.

> [!NOTE]
>
> You can use the [Swagger Editor](https://editor.swagger.io/) to and test the generated `swagger.yaml` file.
>
> A [Swagger UI Action](https://github.com/marketplace/actions/swagger-ui-action) workflow is used to deploy the API documentation to GitHub Pages automatically when a push is made to the `main` branch.

# Framework

A custom framework is used to build the API, which relies on decorators to mark functions as API endpoints. Read more about the [Framework](docs/framework.md).
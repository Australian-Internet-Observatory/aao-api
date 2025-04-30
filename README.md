# Australian Ad Observatory API

This is the codebase for the Australian Ad Observatory API, which is a Mono-Lambda serverless application that provides an API for the [Australian Ad Observatory dashboard](https://github.com/ADMSCentre/australian-ad-observatory-dashboard-v2).

This also hosts the [documentation](https://admscentre.github.io/australian-ad-observatory-api) of the Australian Ad Observatory API.

## Setup

1. Create a `config.ini` file in the root directory of the project to store the AWS credentials and other settings. An example `sample_config.ini` is provided for reference.

2. Use [AWS SAM CLI](https://github.com/aws/aws-sam-cli) to run the API locally.

    2.1. Install AWS SAM CLI for your OS by following the [installation instructions](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html#install-sam-cli-instructions).

    2.2 Run the following command to build the API:

    ```bash
    sam build
    ```

    2.3 Run the following command to start the API locally:

    ```bash
    sam local start-api
    ```

    2.4 The API will be available at `http://localhost:3000/`.

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

To run the unit tests, you can use the following command:

```bash
python -m unittest
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
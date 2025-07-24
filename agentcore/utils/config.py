# ###################################################################################
# Business Source License 1.1

# This file is licensed under the Business Source License 1.1 (BSL 1.1). 
# You may not use this file except in compliance with the License.

# You may obtain a copy of the License at:
# https://mariadb.com/bsl11

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.

# Change Date: 2028-08-01 (3 years from initial release)

# On the Change Date, the License will change to a specified open source license:
# Apache License, Version 2.0

# Original Developer: CoreOps.AI 
# Original License Date: 2025-07-24
# ###################################################################################

from pathlib import Path

CONFIG_DIR = Path.home() / ".agentcore"
CONFIG_FILE = CONFIG_DIR / "config.json"

USERS_ENDPOINT = "/api/users/"
PROJECTS_ENDPOINT = "/api/projects/"
TOKEN_ENDPOINT = "/api/token/"
AWS_INSTANCE_ENDPOINT = "/api/instances/"
PROJECT_INSTANCE_VIEW = "/api/project-instances/"
CREDENTIALS_ENDPOINT="api/aws-credentials/"
AWS_PRICING_ENDPOINT = "api/pricing/"
AWS_REGIONS_ENDPOINT = "api/aws-regions/"
AWS_INSTANCE_TYPES_ENDPOINT = "api/aws/instance-types/"
DATA_ENDPOINT = "api/data/"
ROLES_ENDPOINT = "api/roles/"
EXPERIMENTS_ENDPOINT = "/api/experiments/"
HYPERPARAMETERS_ENDPOINT = "/api/hyperparameters/"
PROJECT_TYPES_ENDPOINT = "/api/project-types/"
PROJECT_TYPE_MODELS_ENDPOINT = "/api/model-types/"
#DATA_VERSION_ENDPOINT = "api/data-version/"
FORGOT_PASSWORD_ENDPOINT= "api/forgot-password/"
VERIFY_OTP_ENDPOINT = "api/verify-otp/"
RESET_PASSOWRD_ENDPOINT = "api/reset-password/"
DATA_VERSION_PROCESSED_ENDPOINT = "api/data-version-processed/"
PROJECT_EXPERIMENTS_ENDPOINT = "/api/projects/{}/experiments/"
DATA_SOURCE_ENDPOINT = "api/data-source/"
EXPERIMENTS_METRICS_ENDPOINT = "api/metrics/"
EXPERIMENT_SETUP_ENDPOINT = "api/instance-setup/"
EXPERIMENT_RUN_ENDPOINT = "api/run-experiment/"
DATASOURCE_ENDPOINT = "api/datasources/"
DATASOURCE_TYPES_ENDPOINT = "api/data-source-types/"
DATAVERSION_ENDPOINT = "api/dataversions"
FETCH_DATA_MONGO_ENDPOINT = "api/mongodb-data/"
OPERATIONS_FE_ENDPOINT = "api/operations/feature-engineering/"
EXPERIMENT_IMAGE_ENDPOINT = "api/experiments/"
DATA_VERSION_ENDPOINT = '/api/data-versions/'
FETCH_INITIAL_DATA_ENDPOINT = '/api/data-versions/fetch/'
PREVIEW_DATA_SOURCE_ENDPOINT = '/api/data-sources/preview/'  # Changed to match your URL pattern
PREVIEW_DATA_VERSION_ENDPOINT = '/api/data-versions/{version_id}/preview/'  # Added version_id parameter
TRANSFORM_DATA_VERSION_ENDPOINT = '/api/data-versions/transform/'
DIAGNOSE_DATA_VERSION_ENDPOINT = '/api/data-versions/{version_id}/quality/'  # Changed to match your URL pattern
TASK_STATUS_ENDPOINT = '/api/data-versions/status/'  # Changed to match your URL pattern
OPERATIONS_ENDPOINT = '/api/operations/'
HISTORY_DATA_VERSION_ENDPOINT = '/api/data-versions/{version_id}/history/'  # Changed to match your URL pattern
METRICS_ENDPOINT = 'api/fastapi-metrics/'
DATA_VERSIONS_ENDPOINT = "/api/data-versions/project/{project_id}/"
FETCH_COLUMNS_ENDPOINT = "/api/fetch-columns/{data_source_id}/"
MODEL_HYPERPARAMETERS_ENDPOINT = "/api/model-hyperparameters/{model_type_id}/"
MODEL_TYPES_ENDPOINT = "api/model-types/project-type/{project_type_id}/"
ALL_MODEL_TYPES_ENDPOINT = "api/model-types/"
RUN_EXPERIMENT_ENDPOINT = "/api/experiment/init/"
RUN_EXPERIMENT_ENDPOINT = "/api/experiment/run-new-experiment/"
LOGS_ENDPOINT = "/api/logs/{experiment_id}/?instance_id={instance_id}&project_id={project_id}"
METRICS_POST = "/api/metrics/"
METRICS_GET = "/api/metrics/{experiment_id}"
ARTIFACTS_ENDPOINT = "/api/experiments/artifacts/list/?instance_id={instance_id}&experiment_id={experiment_id}"
ARTIFACT_DOWNLOAD_ENDPOINT = "/api/experiments/artifact/?instance_id={instance_id}&experiment_id={experiment_id}&filename={filename}"
PROJECT_ARCHIVE_ENDPOINT = "api/projects/{project_id}/archive/"
VALIDATE_URL = "api/ping-agentcore/"
USER_ME_ENDPOINT = "api/users/me"
EXPERIMENT_FETCH= "/api/experiment/artifacts/fetch/"
EXPERIMENT_STATUS= "/api/experiments/{experiment_id}/status/"
USER_ME_ENDPOINT = "api/users/me"
EXPERIMENT_FETCH= "/api/experiment/artifacts/fetch/"
OS_TYPES_ENDPOINT = "api/os-types/"
INSTANCE_STATUS = "api/data-versions/status/"
FETCH_LOGS_ENDPOINT = "/api/experiment/fetch/logs?project_id={project_id}&experiment_group_code={experiment_group_code}&version={version}"
PROMOTE_ENDPOINT = "/api/experiment/promote/"
AWS_CONFIG_CREDENTIALS = "api/aws-credentials/"
RERUN_EXPERIMENT_ENDPOINT = "/api/experiment/re-run-experiment/"
INSTANCE_UPDATE = "api/update-instances/"
CREDENTIALS_TYPES = "/api/credential-types/"
CREDENTIALS_USERS = "/api/users/{user_id}/credentials/"
PROJECT_METRICS_GET = "api/testmetrics?project_id={project_id}"
PROJECT_METRICS_POST = "api/testmetrics/"
METRIC_DEFINITIONS_ENDPOINT = "api/metric-definitions/"
GITPUSH_EXPERIMENT_ENDPOINT = "api/github/push/"
AWS_CREDENTIALS_ENDPOINT = "api/aws-credentials/by-project"
DEPLOY_CREATE_ENDPOINT = "api/promote-experiment/"
FETCH_DEPLOY_STATUS_ENDPOINT = "api/deployment/jobs/{job_id}/status/"
FETCH_DEPLOYMENTS_ENDPOINT = "api/deployment-jobs/"
DEPLOYMENT_PROMOTE_ENDPOINT = "api/promote/"
FETCH_DEPLOYMENT_JOB_ID_ENDPOINT= "api/deployment-jobs/"
OPERATION_METRICS_ENDPOINT = "/api/operational/pro-metrics"
PROJECT_DETAILS_ENDPOINT = "/api/project-details/"
COMPARE_METRICS_DEPLOYMENT_ENDPOINT = "api/deployment/compare-metrics/{deployment_experiemnt_runid}/"
SIGNUP_ENDPOINT = "api/auth/signup/"
TERM_CONDITIONS_ENDPOINT = "term-conditions/"
PRIVACY_POLICY_ENDPOINT = "privacy-policy/"
DEPLOYMENT_STATUS_OVERRIDE_ENDPOINT = "api/deployment/modify_is_test_passed/{experiment_job_id}"
OBSERVABILITY_METRICS_ENDPOINT = "api/operational/pro-metrics"
DEPLOYMENT_LISTING_ENDPOINT = "api/models-hub-prod"
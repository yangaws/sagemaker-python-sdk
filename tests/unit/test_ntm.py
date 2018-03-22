# Copyright 2017 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.
import pytest
from mock import Mock, patch

from sagemaker.amazon.ntm import NTM, NTMPredictor
from sagemaker.amazon.amazon_estimator import registry, RecordSet

ROLE = 'myrole'
TRAIN_INSTANCE_COUNT = 1
TRAIN_INSTANCE_TYPE = 'ml.c4.xlarge'
NUM_TOPICS = 5

COMMON_TRAIN_ARGS = {'role': ROLE, 'train_instance_count': TRAIN_INSTANCE_COUNT,
                     'train_instance_type': TRAIN_INSTANCE_TYPE}
ALL_REQ_ARGS = dict({'num_topics': NUM_TOPICS}, **COMMON_TRAIN_ARGS)

REGION = "us-west-2"
BUCKET_NAME = "Some-Bucket"

DESCRIBE_TRAINING_JOB_RESULT = {
    'ModelArtifacts': {
        'S3ModelArtifacts': "s3://bucket/model.tar.gz"
    }
}


@pytest.fixture()
def sagemaker_session():
    boto_mock = Mock(name='boto_session', region_name=REGION)
    sms = Mock(name='sagemaker_session', boto_session=boto_mock)
    sms.boto_region_name = REGION
    sms.default_bucket = Mock(name='default_bucket', return_value=BUCKET_NAME)
    sms.sagemaker_client.describe_training_job = Mock(name='describe_training_job',
                                                      return_value=DESCRIBE_TRAINING_JOB_RESULT)

    return sms


def test_init_required_positional(sagemaker_session):
    ntm = NTM(ROLE, TRAIN_INSTANCE_COUNT, TRAIN_INSTANCE_TYPE, NUM_TOPICS, sagemaker_session=sagemaker_session)
    assert ntm.role == ROLE
    assert ntm.train_instance_count == TRAIN_INSTANCE_COUNT
    assert ntm.train_instance_type == TRAIN_INSTANCE_TYPE
    assert ntm.num_topics == NUM_TOPICS


def test_init_required_named(sagemaker_session):
    ntm = NTM(sagemaker_session=sagemaker_session, **ALL_REQ_ARGS)

    assert ntm.role == COMMON_TRAIN_ARGS['role']
    assert ntm.train_instance_count == TRAIN_INSTANCE_COUNT
    assert ntm.train_instance_type == COMMON_TRAIN_ARGS['train_instance_type']
    assert ntm.num_topics == ALL_REQ_ARGS['num_topics']


def test_all_hyperparameters(sagemaker_session):
    ntm = NTM(sagemaker_session=sagemaker_session,
              encoder_layers=[1, 2, 3], epochs=3, encoder_layers_activation='tanh', optimizer='sgd',
              tolerance=0.05, num_patience_epochs=2, batch_norm=False, rescale_gradient=0.5, clip_gradient=0.5,
              weight_decay=0.5, learning_rate=0.5, **ALL_REQ_ARGS)
    assert ntm.hyperparameters() == dict(
        num_topics=str(ALL_REQ_ARGS['num_topics']),
        encoder_layers='[1, 2, 3]',
        epochs='3',
        encoder_layers_activation='tanh',
        optimizer='sgd',
        tolerance='0.05',
        num_patience_epochs='2',
        batch_norm='False',
        rescale_gradient='0.5',
        clip_gradient='0.5',
        weight_decay='0.5',
        learning_rate='0.5'
    )


def test_image(sagemaker_session):
    ntm = NTM(sagemaker_session=sagemaker_session, **ALL_REQ_ARGS)
    assert ntm.train_image() == registry(REGION, "ntm") + '/ntm:1'


@pytest.mark.parametrize('required_hyper_parameters, value', [
    ('num_topics', 'string')
])
def test_required_hyper_parameters_type(sagemaker_session, required_hyper_parameters, value):
    with pytest.raises(ValueError):
        test_params = ALL_REQ_ARGS.copy()
        test_params[required_hyper_parameters] = value
        NTM(sagemaker_session=sagemaker_session, **test_params)


@pytest.mark.parametrize('required_hyper_parameters, value', [
    ('num_topics', 0),
    ('num_topics', 10000)
])
def test_required_hyper_parameters_value(sagemaker_session, required_hyper_parameters, value):
    with pytest.raises(ValueError):
        test_params = ALL_REQ_ARGS.copy()
        test_params[required_hyper_parameters] = value
        NTM(sagemaker_session=sagemaker_session, **test_params)


@pytest.mark.parametrize('iterable_hyper_parameters, value', [
    ('encoder_layers', 0)
])
def test_iterable_hyper_parameters_type(sagemaker_session, iterable_hyper_parameters, value):
    with pytest.raises(TypeError):
        test_params = ALL_REQ_ARGS.copy()
        test_params.update({iterable_hyper_parameters: value})
        NTM(sagemaker_session=sagemaker_session, **test_params)


@pytest.mark.parametrize('optional_hyper_parameters, value', [
    ('epochs', 'string'),
    ('encoder_layers_activation', 0),
    ('optimizer', 0),
    ('tolerance', 'string'),
    ('num_patience_epochs', 'string'),
    ('rescale_gradient', 'string'),
    ('clip_gradient', 'string'),
    ('weight_decay', 'string'),
    ('learning_rate', 'string')
])
def test_optional_hyper_parameters_type(sagemaker_session, optional_hyper_parameters, value):
    with pytest.raises(ValueError):
        test_params = ALL_REQ_ARGS.copy()
        test_params.update({optional_hyper_parameters: value})
        NTM(sagemaker_session=sagemaker_session, **test_params)


@pytest.mark.parametrize('optional_hyper_parameters, value', [
    ('epochs', 0),
    ('epochs', 1000),
    ('encoder_layers_activation', 'string'),
    ('optimizer', 'string'),
    ('tolerance', 0),
    ('tolerance', 0.5),
    ('num_patience_epochs', 0),
    ('num_patience_epochs', 100),
    ('rescale_gradient', 0),
    ('rescale_gradient', 10),
    ('clip_gradient', 0),
    ('weight_decay', -1),
    ('weight_decay', 2),
    ('learning_rate', 0),
    ('learning_rate', 2)
])
def test_optional_hyper_parameters_value(sagemaker_session, optional_hyper_parameters, value):
    with pytest.raises(ValueError):
        test_params = ALL_REQ_ARGS.copy()
        test_params.update({optional_hyper_parameters: value})
        NTM(sagemaker_session=sagemaker_session, **test_params)


PREFIX = "prefix"
FEATURE_DIM = 10
MINI_BATCH_SIZE = 200


@patch("sagemaker.amazon.amazon_estimator.AmazonAlgorithmEstimatorBase.fit")
def test_call_fit(base_fit, sagemaker_session):
    ntm = NTM(base_job_name="ntm", sagemaker_session=sagemaker_session, **ALL_REQ_ARGS)

    data = RecordSet("s3://{}/{}".format(BUCKET_NAME, PREFIX), num_records=1, feature_dim=FEATURE_DIM, channel='train')

    ntm.fit(data, MINI_BATCH_SIZE)

    base_fit.assert_called_once()
    assert len(base_fit.call_args[0]) == 2
    assert base_fit.call_args[0][0] == data
    assert base_fit.call_args[0][1] == MINI_BATCH_SIZE


def test_call_fit_none_mini_batch_size(sagemaker_session):
    ntm = NTM(base_job_name="ntm", sagemaker_session=sagemaker_session, **ALL_REQ_ARGS)

    data = RecordSet("s3://{}/{}".format(BUCKET_NAME, PREFIX), num_records=1, feature_dim=FEATURE_DIM,
                     channel='train')
    ntm.fit(data)


def test_call_fit_wrong_type_mini_batch_size(sagemaker_session):
    ntm = NTM(base_job_name="ntm", sagemaker_session=sagemaker_session, **ALL_REQ_ARGS)

    data = RecordSet("s3://{}/{}".format(BUCKET_NAME, PREFIX), num_records=1, feature_dim=FEATURE_DIM,
                     channel='train')

    with pytest.raises((TypeError, ValueError)):
        ntm.fit(data, "some")


def test_call_fit_wrong_value_lower_mini_batch_size(sagemaker_session):
    ntm = NTM(base_job_name="ntm", sagemaker_session=sagemaker_session, **ALL_REQ_ARGS)

    data = RecordSet("s3://{}/{}".format(BUCKET_NAME, PREFIX), num_records=1, feature_dim=FEATURE_DIM,
                     channel='train')
    with pytest.raises(ValueError):
        ntm.fit(data, 0)


def test_call_fit_wrong_value_upper_mini_batch_size(sagemaker_session):
    ntm = NTM(base_job_name="ntm", sagemaker_session=sagemaker_session, **ALL_REQ_ARGS)

    data = RecordSet("s3://{}/{}".format(BUCKET_NAME, PREFIX), num_records=1, feature_dim=FEATURE_DIM,
                     channel='train')
    with pytest.raises(ValueError):
        ntm.fit(data, 10001)


def test_model_image(sagemaker_session):
    ntm = NTM(sagemaker_session=sagemaker_session, **ALL_REQ_ARGS)
    data = RecordSet("s3://{}/{}".format(BUCKET_NAME, PREFIX), num_records=1, feature_dim=FEATURE_DIM, channel='train')
    ntm.fit(data, MINI_BATCH_SIZE)

    model = ntm.create_model()
    assert model.image == registry(REGION, "ntm") + '/ntm:1'


def test_predictor_type(sagemaker_session):
    ntm = NTM(sagemaker_session=sagemaker_session, **ALL_REQ_ARGS)
    data = RecordSet("s3://{}/{}".format(BUCKET_NAME, PREFIX), num_records=1, feature_dim=FEATURE_DIM, channel='train')
    ntm.fit(data, MINI_BATCH_SIZE)
    model = ntm.create_model()
    predictor = model.deploy(1, TRAIN_INSTANCE_TYPE)

    assert isinstance(predictor, NTMPredictor)

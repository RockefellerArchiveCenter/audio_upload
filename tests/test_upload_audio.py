from pathlib import Path
from shutil import copytree, rmtree
from unittest.mock import patch

import pytest

from src.upload_audio import create_tarball, main, remove_unwanted_files

BAG_REFID = "b90862f3baceaae3b7418c78f9d50d52"

DEFAULT_ARGS = [
    BAG_REFID,
    'aws:iam:role:internal-digitization-role',
    'rac-dev-digitized-image-upload',
    '/local_storage']

FIXTURE_PATH = Path("tests", "fixtures", BAG_REFID)
TMP_PATH = Path("tmp", BAG_REFID)


@pytest.fixture()
def file_fixture():
    """Fixture to create and tear down dir before and after a test is run"""
    copytree(FIXTURE_PATH, TMP_PATH)

    yield  # this is where the testing happens

    if TMP_PATH.is_dir():
        rmtree(TMP_PATH)


@patch('src.upload_audio.remove_unwanted_files')
@patch('src.upload_audio.create_bag')
@patch('src.upload_audio.create_tarball')
@patch('src.upload_audio.upload_package')
def test_main_with_dir(mock_upload, mock_tarball, mock_create_bag, mock_unwanted):
    current_dir = Path('/local_storage', BAG_REFID)
    tarball_path = f'/local_storage/{BAG_REFID}.tar.gz'
    mock_tarball.return_value = tarball_path
    Path(current_dir).mkdir(parents=True)

    main(*DEFAULT_ARGS)

    mock_unwanted.assert_called_once_with(current_dir)
    mock_create_bag.assert_called_once_with(str(current_dir))
    mock_tarball.assert_called_once_with(current_dir)
    mock_upload.assert_called_once_with(
        tarball_path,
        'rac-dev-digitized-image-upload',
        'aws:iam:role:internal-digitization-role')
    rmtree(current_dir)


def test_remove_unwanted_files(file_fixture):
    initial_file_count = len(list(TMP_PATH.rglob('*')))

    for dir in ['master', 'service_edited']:
        for filename in ['.DS_Store', 'Thumbs.db']:
            with open(TMP_PATH / dir / filename, 'w') as fp:
                fp.write('test')

    remove_unwanted_files(TMP_PATH)

    processed_file_count = len(list(TMP_PATH.rglob('*')))
    assert initial_file_count == processed_file_count


def test_create_tarball():
    current_dir = Path("/current/dir")
    current_dir.mkdir(parents=True)
    create_tarball(current_dir)
    assert Path('/current/dir.tar.gz').is_file()
    assert not current_dir.exists()

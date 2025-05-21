import pytest
from unittest.mock import AsyncMock, MagicMock, patch, ANY

from fastapi import HTTPException, status

from app.core.jwt import create_access_token, verify_access_token, auth
from app.crud.user import create_user, get_user_by_username, get_user_by_id
from app.crud.org import get_organization_by_name, get_all_organizations, get_user_org_membership
from app.crud.cluster import get_cluster, list_clusters, delete_cluster
from app.crud.deployment import get_deployment_by_id_for_scheduling
from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.models.Organization import Organization
from app.models.UserOrganizations import UserOrganization
from app.models.Cluster import Cluster
from app.models.Deployment import Deployment
from app.models.Role import RoleEnum
from app.config import SECRET_KEY


@pytest.fixture(autouse=True)
def patch_jwt_secret():
    patcher = patch("app.config.SECRET_KEY", "testsecret")
    patcher.start()
    yield
    patcher.stop()

@pytest.fixture
def dummy_user():
    user_mock = MagicMock()
    user_mock.username = "alice"
    user_mock.id = 42
    user_mock.hashed_password = "hashedpwd"
    return user_mock

@pytest.fixture
def dummy_org():
    org_mock = MagicMock()
    org_mock.id = 1
    org_mock.name = "TestOrg"
    return org_mock

@pytest.fixture
def dummy_membership(dummy_user, dummy_org):
    membership_mock = MagicMock()
    membership_mock.user_id = dummy_user.id
    membership_mock.organization_id = dummy_org.id
    membership_mock.role = RoleEnum.Admin
    return membership_mock

@pytest.fixture
def dummy_cluster(dummy_user, dummy_org):
    cluster_mock = MagicMock()
    cluster_mock.id = 101
    cluster_mock.name = "TestCluster"
    cluster_mock.owner_id = dummy_user.id
    cluster_mock.organization_id = dummy_org.id
    return cluster_mock

@pytest.fixture
def dummy_deployment(dummy_user, dummy_cluster):
    deployment_mock = MagicMock()
    deployment_mock.id = 201
    deployment_mock.owner_id = dummy_user.id
    deployment_mock.cluster_id = dummy_cluster.id
    return deployment_mock

class DummyResult: 
    def __init__(self, value):
        self._value = value
        self._scalars_called = False

    def scalar_one_or_none(self):
        return self._value

    def scalars(self):
        self._scalars_called = True
        return self

    def all(self):
        if not self._scalars_called:
             raise AttributeError("Need to call .scalars() first")
        if isinstance(self._value, list):
            return self._value
        return [self._value] if self._value is not None else []

    def first(self):
        if not self._scalars_called:
             raise AttributeError("Need to call .scalars() first")
        if isinstance(self._value, list):
            return self._value[0] if self._value else None
        return self._value

@pytest.mark.test
def test_create_and_verify_access_token():
    payload = {"sub": "alice", "user_id": 42}
    token = create_access_token(payload)
    decoded = verify_access_token(token)
    assert decoded["sub"] == "alice"
    assert decoded["user_id"] == 42

@pytest.mark.test
def test_verify_access_token_invalid():
    bad = "xxx.invalid.token"
    assert verify_access_token(bad) is None



@pytest.mark.asyncio
@pytest.mark.test
async def test_get_user_by_username_found(monkeypatch, dummy_user):
    fake_session = AsyncMock()
    fake_session.execute.return_value = DummyResult(dummy_user)

    u = await get_user_by_username(fake_session, "alice")
    assert u is dummy_user
    fake_session.execute.assert_awaited_once()

@pytest.mark.asyncio
@pytest.mark.test
async def test_get_user_by_username_not_found(monkeypatch):
    fake_session = AsyncMock()
    fake_session.execute.return_value = DummyResult(None)

    u = await get_user_by_username(fake_session, "nobody")
    assert u is None
    fake_session.execute.assert_awaited_once()

@pytest.mark.asyncio
@pytest.mark.test
async def test_get_user_by_id_found(monkeypatch, dummy_user):
    fake_session = AsyncMock()
    fake_session.execute.return_value = DummyResult(dummy_user)

    u = await get_user_by_id(fake_session, 42)
    assert u is dummy_user
    fake_session.execute.assert_awaited_once()

@pytest.mark.asyncio
@pytest.mark.test
async def test_get_user_by_id_not_found(monkeypatch):
    fake_session = AsyncMock()
    fake_session.execute.return_value = DummyResult(None)

    u = await get_user_by_id(fake_session, 999)
    assert u is None
    fake_session.execute.assert_awaited_once()


@pytest.mark.asyncio
@pytest.mark.test
async def test_auth_invalid_token(monkeypatch):
    monkeypatch.setattr("app.core.jwt.verify_access_token", lambda t: None)
    
    with pytest.raises(HTTPException) as excinfo:
        await auth(token="bad", db=AsyncMock())
    assert excinfo.value.status_code == status.HTTP_401_UNAUTHORIZED



@pytest.mark.asyncio
@pytest.mark.test
async def test_get_organization_by_name_found(monkeypatch, dummy_org):
    fake_session = AsyncMock()
    fake_session.execute.return_value = DummyResult(dummy_org)

    org = await get_organization_by_name(fake_session, "TestOrg")
    assert org is dummy_org
    fake_session.execute.assert_awaited_once()

@pytest.mark.asyncio
@pytest.mark.test
async def test_get_organization_by_name_not_found(monkeypatch):
    fake_session = AsyncMock()
    fake_session.execute.return_value = DummyResult(None)

    org = await get_organization_by_name(fake_session, "NonExistentOrg")
    assert org is None
    fake_session.execute.assert_awaited_once()

@pytest.mark.asyncio
@pytest.mark.test
async def test_get_all_organizations(monkeypatch, dummy_org):
    fake_session = AsyncMock()
    fake_session.execute.return_value = DummyResult([dummy_org, MagicMock()]) # Mock multiple orgs

    orgs = await get_all_organizations(fake_session)
    assert len(orgs) == 2
    assert orgs[0] is dummy_org
    fake_session.execute.assert_awaited_once()

@pytest.mark.asyncio
@pytest.mark.test
async def test_get_user_org_membership_found(monkeypatch, dummy_membership):
    fake_session = AsyncMock()
    fake_session.execute.return_value = DummyResult(dummy_membership)

    membership = await get_user_org_membership(fake_session, 42, 1)
    assert membership is dummy_membership
    fake_session.execute.assert_awaited_once()

@pytest.mark.asyncio
@pytest.mark.test
async def test_get_user_org_membership_not_found(monkeypatch):
    fake_session = AsyncMock()
    fake_session.execute.return_value = DummyResult(None)

    membership = await get_user_org_membership(fake_session, 999, 999)
    assert membership is None
    fake_session.execute.assert_awaited_once()

@pytest.mark.asyncio
@pytest.mark.test
async def test_get_cluster_found(monkeypatch, dummy_user, dummy_cluster):
    fake_session = AsyncMock()
    fake_session.execute.return_value = DummyResult(dummy_cluster)

    cluster = await get_cluster(fake_session, dummy_user, dummy_cluster.id)
    assert cluster is dummy_cluster
    fake_session.execute.assert_awaited_once()

@pytest.mark.asyncio
@pytest.mark.test
async def test_get_cluster_not_found(monkeypatch, dummy_user):
    fake_session = AsyncMock()
    fake_session.execute.return_value = DummyResult(None)

    with pytest.raises(HTTPException) as excinfo:
        await get_cluster(fake_session, dummy_user, 999)
    assert excinfo.value.status_code == 404
    fake_session.execute.assert_awaited_once()

@pytest.mark.asyncio
@pytest.mark.test
async def test_list_clusters_all(monkeypatch, dummy_user, dummy_cluster):
    fake_session = AsyncMock()
    fake_session.execute.return_value = DummyResult([dummy_cluster, MagicMock()])

    clusters = await list_clusters(fake_session, dummy_user)
    assert len(clusters) == 2
    assert clusters[0] is dummy_cluster
    fake_session.execute.assert_awaited_once()

@pytest.mark.asyncio
@pytest.mark.test
async def test_list_clusters_filtered_by_org(monkeypatch, dummy_user, dummy_cluster):
    fake_session = AsyncMock()
    fake_session.execute.return_value = DummyResult([dummy_cluster]) # Only one cluster in this org

    clusters = await list_clusters(fake_session, dummy_user, org_id=dummy_cluster.organization_id)
    assert len(clusters) == 1
    assert clusters[0] is dummy_cluster
    fake_session.execute.assert_awaited_once()

@pytest.mark.asyncio
@pytest.mark.test
async def test_delete_cluster_success(monkeypatch, dummy_user, dummy_cluster):
    fake_session = AsyncMock()
    fake_session.execute.return_value = DummyResult(dummy_cluster)
    
    await delete_cluster(fake_session, dummy_user, dummy_cluster.id)
    fake_session.execute.assert_awaited_once()
    fake_session.delete.assert_called_once_with(dummy_cluster)
    fake_session.commit.assert_awaited_once()

@pytest.mark.asyncio
@pytest.mark.test
async def test_delete_cluster_not_found(monkeypatch, dummy_user):
    fake_session = AsyncMock()
    fake_session.execute.return_value = DummyResult(None)

    with pytest.raises(HTTPException) as excinfo:
        await delete_cluster(fake_session, dummy_user, 999)
    assert excinfo.value.status_code == 404
    fake_session.execute.assert_awaited_once()
    fake_session.delete.assert_not_called()
    fake_session.commit.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.test
async def test_get_deployment_by_id_for_scheduling_found(monkeypatch, dummy_deployment):
    fake_session = AsyncMock()
    fake_session.execute.return_value = DummyResult(dummy_deployment)

    dep = await get_deployment_by_id_for_scheduling(fake_session, dummy_deployment.id)
    assert dep is dummy_deployment
    fake_session.execute.assert_awaited_once()

@pytest.mark.asyncio
@pytest.mark.test
async def test_get_deployment_by_id_for_scheduling_not_found(monkeypatch):
    fake_session = AsyncMock()
    fake_session.execute.return_value = DummyResult(None)

    dep = await get_deployment_by_id_for_scheduling(fake_session, 999)
    assert dep is None
    fake_session.execute.assert_awaited_once()



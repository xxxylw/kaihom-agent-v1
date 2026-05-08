from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session

from app.db.session import get_session
from app.schemas.mock_kaihong import (
    MockCustomerResponse,
    MockDictionariesResponse,
    MockDraftCreateRequest,
    MockDraftResponse,
    MockLoginRequest,
    MockRecentOrderResponse,
    MockTokenResponse,
    MockUserResponse,
)
from app.services import mock_kaihong


router = APIRouter(prefix="/mock/kaihong", tags=["Mock Kaihong"])
bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> MockUserResponse:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
        )

    user = mock_kaihong.get_user_by_token(credentials.credentials)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid bearer token",
        )
    return user


@router.post("/auth/login", response_model=MockTokenResponse)
def login(request: MockLoginRequest) -> MockTokenResponse:
    user = mock_kaihong.authenticate_user(request.username, request.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    return MockTokenResponse(access_token=mock_kaihong.token_for_user(user))


@router.get("/users/me", response_model=MockUserResponse)
def read_current_user(
    current_user: MockUserResponse = Depends(get_current_user),
) -> MockUserResponse:
    return current_user


@router.get("/customers", response_model=list[MockCustomerResponse])
def list_customers(
    q: str | None = None,
    current_user: MockUserResponse = Depends(get_current_user),
) -> list[MockCustomerResponse]:
    return mock_kaihong.list_customers(q)


@router.get("/customers/{customer_id}", response_model=MockCustomerResponse)
def get_customer(
    customer_id: str,
    current_user: MockUserResponse = Depends(get_current_user),
) -> MockCustomerResponse:
    customer = mock_kaihong.get_customer(customer_id)
    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        )
    return customer


@router.get("/dictionaries", response_model=MockDictionariesResponse)
def get_dictionaries(
    current_user: MockUserResponse = Depends(get_current_user),
) -> MockDictionariesResponse:
    return mock_kaihong.get_dictionaries()


@router.get(
    "/customers/{customer_id}/recent-orders",
    response_model=list[MockRecentOrderResponse],
)
def list_recent_orders(
    customer_id: str,
    current_user: MockUserResponse = Depends(get_current_user),
) -> list[MockRecentOrderResponse]:
    if mock_kaihong.get_customer(customer_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        )
    return mock_kaihong.list_recent_orders(customer_id)


@router.post(
    "/drafts",
    response_model=MockDraftResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_draft(
    request: MockDraftCreateRequest,
    session: Session = Depends(get_session),
    current_user: MockUserResponse = Depends(get_current_user),
) -> MockDraftResponse:
    if mock_kaihong.get_customer(request.customer_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        )
    return mock_kaihong.create_draft(session, request)


@router.get("/drafts/{draft_id}", response_model=MockDraftResponse)
def get_draft(
    draft_id: str,
    session: Session = Depends(get_session),
    current_user: MockUserResponse = Depends(get_current_user),
) -> MockDraftResponse:
    draft = mock_kaihong.get_draft(session, draft_id)
    if draft is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Draft not found",
        )
    return draft

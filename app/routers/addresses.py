from fastapi import APIRouter, Depends, HTTPException, Path, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Address, Contact
from app.schemas import AddressCreate, AddressRead, AddressUpdate, ErrorResponse

router = APIRouter(prefix="/api/v1", tags=["addresses"])

ADDRESS_ID = Path(description="Address identifier.", examples=[1], ge=1)
CONTACT_ID = Path(description="Contact identifier.", examples=[1], ge=1)

NOT_FOUND_ADDRESS = {
    "model": ErrorResponse,
    "description": "No address exists with that id.",
    "content": {"application/json": {"example": {"detail": "Address 42 not found"}}},
}

NOT_FOUND_CONTACT = {
    "model": ErrorResponse,
    "description": "No contact exists with that id.",
    "content": {"application/json": {"example": {"detail": "Contact 42 not found"}}},
}


def _get_contact_or_404(db: Session, contact_id: int) -> Contact:
    contact = db.get(Contact, contact_id)
    if contact is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Contact {contact_id} not found")
    return contact


def _get_address_or_404(db: Session, address_id: int) -> Address:
    address = db.get(Address, address_id)
    if address is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Address {address_id} not found")
    return address


@router.post(
    "/contacts/{contact_id}/addresses",
    response_model=AddressRead,
    status_code=status.HTTP_201_CREATED,
    operation_id="createAddress",
    summary="Create an address for a contact",
    response_description="The stored address, including its new id and timestamps.",
    responses={status.HTTP_404_NOT_FOUND: NOT_FOUND_CONTACT},
)
def create_address(
    payload: AddressCreate,
    contact_id: int = CONTACT_ID,
    db: Session = Depends(get_db),
) -> Address:
    """Create a new address for the specified contact."""
    _get_contact_or_404(db, contact_id)

    address = Address(contact_id=contact_id, **payload.model_dump())
    db.add(address)
    db.commit()
    db.refresh(address)
    return address


@router.get(
    "/contacts/{contact_id}/addresses",
    response_model=list[AddressRead],
    operation_id="listAddresses",
    summary="List addresses for a contact",
    response_description="All addresses for the contact.",
    responses={status.HTTP_404_NOT_FOUND: NOT_FOUND_CONTACT},
)
def list_addresses(
    contact_id: int = CONTACT_ID,
    db: Session = Depends(get_db),
) -> list[Address]:
    """Get all addresses for a specific contact."""
    contact = _get_contact_or_404(db, contact_id)
    return contact.addresses


@router.get(
    "/addresses/{address_id}",
    response_model=AddressRead,
    operation_id="getAddress",
    summary="Get an address",
    response_description="The requested address.",
    responses={status.HTTP_404_NOT_FOUND: NOT_FOUND_ADDRESS},
)
def get_address(
    address_id: int = ADDRESS_ID,
    db: Session = Depends(get_db),
) -> Address:
    """Fetch a single address by its id."""
    return _get_address_or_404(db, address_id)


@router.patch(
    "/addresses/{address_id}",
    response_model=AddressRead,
    operation_id="updateAddress",
    summary="Partially update an address",
    response_description="The address after the update.",
    responses={status.HTTP_404_NOT_FOUND: NOT_FOUND_ADDRESS},
)
def update_address(
    payload: AddressUpdate,
    address_id: int = ADDRESS_ID,
    db: Session = Depends(get_db),
) -> Address:
    """Update only the fields present in the request body."""
    address = _get_address_or_404(db, address_id)

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(address, field, value)

    db.commit()
    db.refresh(address)
    return address


@router.delete(
    "/addresses/{address_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="deleteAddress",
    summary="Delete an address",
    response_description="Deleted; the response has no body.",
    responses={
        status.HTTP_204_NO_CONTENT: {"description": "Deleted; the response has no body."},
        status.HTTP_404_NOT_FOUND: NOT_FOUND_ADDRESS,
    },
)
def delete_address(
    address_id: int = ADDRESS_ID,
    db: Session = Depends(get_db),
) -> Response:
    """Permanently delete an address."""
    address = _get_address_or_404(db, address_id)
    db.delete(address)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

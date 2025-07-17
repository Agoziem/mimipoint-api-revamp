from fastapi import UploadFile, File, HTTPException, Form, APIRouter, Depends
from pydantic import BaseModel
from .utils import upload_multiple_files, upload_or_replace_file, delete_file
from app.api.v1.auth.schemas.schemas import UserResponseModel as UserResponse
from app.api.v1.auth.dependencies import get_current_user

file_router = APIRouter()

@file_router.post("/upload")
async def upload(
    file: UploadFile = File(...),
    key: str = Form(...),
    replace: bool = Form(True),
    _: UserResponse = Depends(get_current_user)
):
    try:
        url = await upload_or_replace_file(file, key=key, replace=replace)
        return {"url": url, "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

class FileDeleteRequestModel(BaseModel):
    file_url: str


@file_router.delete("/delete")
async def delete(data: FileDeleteRequestModel, _: UserResponse = Depends(get_current_user)):
    success = await delete_file(data.file_url)
    if success:
        return {"status": "deleted"}
    else:
        raise HTTPException(status_code=404, detail="File not found or couldn't be deleted")
    

@file_router.post("/upload_multiple")
async def upload_multiple(
    files: list[UploadFile] = File(...),
    keys: list[str] = Form(...),
    replace: bool = Form(True),
    _: UserResponse = Depends(get_current_user)
):
    if len(files) != len(keys):
        raise HTTPException(status_code=400, detail="Number of files and keys must match")
    
    urls = await upload_multiple_files(files, keys, replace)
    return {"urls": urls, "status": "success"}
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from backend.interactors import transaction as transaction_interactors
# from backend.utils.schema import Transaction
from fastapi import UploadFile



# Create a router.
router = APIRouter(prefix="/api")


@router.post("/Add_GL_in_vecdb_pipeline")
async def transaction_pipeline (file: UploadFile):
    try:
        response = await transaction_interactors.add_doc_call(file)
    except Exception as e:
        return JSONResponse(content = {"succeeded": False, "message": f"Error saving file to vetordb : {e}", "status_code": status.HTTP_400_BAD_REQUEST},status_code=status.HTTP_400_BAD_REQUEST)
    return JSONResponse(content = {"succeeded": True, "message": "Succesfully saved file to vectordb", "data": response, "status_code": status.HTTP_200_OK},status_code=status.HTTP_200_OK)
 


@router.post("/get_category")
async def transaction_pipeline (file: UploadFile):
    try:
        response = await transaction_interactors.call(file)
    except Exception as e:
        return JSONResponse(content = {"succeeded": False, "message": f"Error saving file to vetordb : {e}", "status_code": status.HTTP_400_BAD_REQUEST},status_code=status.HTTP_400_BAD_REQUEST)
    return JSONResponse(content = {"succeeded": True, "message": "Succesfully saved file to vectordb", "data": response, "status_code": status.HTTP_200_OK},status_code=status.HTTP_200_OK)
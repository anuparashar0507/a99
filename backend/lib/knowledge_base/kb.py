import logging
import asyncio
import magic  # For file type detection
from typing import Dict, List, Optional, Any  # Added Any for flexibility
from fastapi import UploadFile  # Assuming UploadFile type from FastAPI

from lib.lyzr_rag.lyzr_parse import RawTextType  # Assuming this path is correct
from lib.models.kb_models import (
    KbFileType,
    KnowledgeBaseModel,
)  # Added KnowledgeBaseModel for DB result type hint
from lib.repositories.exceptions import (
    RepositoryReadException,
)

# Assuming LyzrRag, LyzrParse, FileType, DATA_PARSERS, LyzrRagConfig are correctly defined and imported
from ..lyzr_rag import FileType, DATA_PARSERS, LyzrParse, LyzrRag, LyzrRagConfig
from ..repositories.repository_manager_protocol import RepositoryManagerProtocol
from ..s3_handler.s3 import S3Handler

logger = logging.getLogger(__name__)


class KnowledgeBase:
    """
    Service class for managing Knowledge Base operations, including
    configuration, parsing, storage (RAG, S3, DB), and retrieval.
    """

    def __init__(
        self,
        db: RepositoryManagerProtocol,
        rag: LyzrRag,
        parse: LyzrParse,
        s3_handler: S3Handler,
    ):
        """
        Initializes the KnowledgeBase service.

        Args:
            db: Repository Manager instance providing access to repositories.
            rag: Client instance for Lyzr RAG API.
            parse: Client instance for Lyzr Parse API.
            s3_handler: Handler instance for S3 interactions.
        """
        self.db = db
        self.rag = rag
        self.parse = parse
        self.s3 = s3_handler
        # self.logger is already available via module-level logger
        logger.info("KnowledgeBase service initialized.")  # Log successful init

    def get_default_config(self, topic: str, user_id: str) -> LyzrRagConfig:
        """Generates a default configuration dictionary for Lyzr RAG."""
        # This method is simple, logging entry might be excessive unless debugging
        logger.debug(
            f"Generating default RAG config for topic: '{topic}', user: {user_id}"
        )
        config: LyzrRagConfig = {
            "user_id": user_id,
            "description": f"Rag store for topic: {topic}",
            "llm_credential_id": "lyzr_openai",
            "embedding_credential_id": "lyzr_openai",
            "vector_db_credential_id": "lyzr_qdrant",
            "vector_store_provider": "Qdrant [Lyzr]",
            "collection_name": topic,  # Consider making this safer (e.g., slugify, add user prefix)
            "llm_model": "gpt-4o-mini",
            "embedding_model": "text-embedding-ada-002",
            # Added missing fields from TypedDict definition if they are required implicitly
            "semantic_data_model": False,  # Example default
            "meta_data": {},  # Example default
            "id": None,  # Example default
        }
        # Ensure all keys defined in LyzrRagConfig TypedDict are present
        return config

    def _determine_file_type(self, file: UploadFile) -> str:
        """Detects file type (pdf, docx, txt, csv) based on MIME and fallback to extension."""
        try:
            # Read initial chunk for MIME detection
            file_signature = file.file.read(2048)
            # IMPORTANT: Reset file pointer after reading for subsequent operations
            file.file.seek(0)

            if not file_signature:
                logger.warning(f"File '{file.filename}' appears to be empty.")
                # Fallback to extension if file is empty
                return (
                    file.filename.split(".")[-1].lower()
                    if file.filename and "." in file.filename
                    else "unknown"
                )

            mime_map = {
                "application/pdf": "pdf",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
                "application/msword": "doc",  # Added basic .doc detection
                "text/plain": "txt",
                "text/csv": "csv",
            }
            mime_type = magic.Magic(mime=True).from_buffer(file_signature)
            detected_type = mime_map.get(mime_type)

            if detected_type:
                logger.debug(
                    f"Detected file type '{detected_type}' using MIME type '{mime_type}' for file '{file.filename}'."
                )
                return detected_type
            else:
                # Fallback to file extension if MIME type is not in our map
                extension = (
                    file.filename.split(".")[-1].lower()
                    if file.filename and "." in file.filename
                    else "unknown"
                )
                logger.warning(
                    f"MIME type '{mime_type}' not recognized for file '{file.filename}'. Falling back to extension '{extension}'."
                )
                # Validate if extension is one we support, otherwise return 'unknown'
                return (
                    extension
                    if extension in ["pdf", "docx", "txt", "csv", "doc"]
                    else "unknown"
                )

        except Exception as e:
            logger.exception(
                f"Error determining file type for '{file.filename}': {e}", exc_info=True
            )
            # Fallback to extension on error
            extension = (
                file.filename.split(".")[-1].lower()
                if file.filename and "." in file.filename
                else "unknown"
            )
            return (
                extension
                if extension in ["pdf", "docx", "txt", "csv", "doc"]
                else "unknown"
            )

    async def _parse_file_content(
        self, file_type: str, file: UploadFile, api_key: str
    ) -> Optional[List[Dict]]:
        """Parses file content using the appropriate LyzrParse method."""
        logger.info(
            f"Parsing content for file '{file.filename}' using type '{file_type}'."
        )
        content_result: Optional[Dict] = None
        parser_used = DATA_PARSERS.get(file_type, "simple")  # Default to simple parser

        try:
            # Map detected file_type string to FileType enum expected by parse.parse_files
            file_type_enum: Optional[FileType] = None
            try:
                # Assumes FileType enum values match lowercase strings like "pdf", "docx" etc.
                file_type_enum = FileType(file_type)
            except ValueError:
                logger.error(
                    f"Unsupported file type '{file_type}' passed to _parse_file_content for file '{file.filename}'."
                )
                return None  # Cannot parse unsupported type

            # Call the parsing service
            content_result = await self.parse.parse_files(
                file=file,  # Pass the UploadFile object directly if parse_files expects it
                data_parser=parser_used,
                file_type=file_type_enum,  # Pass the Enum member
                api_key=api_key,
            )

            # Validate the response structure
            if (
                content_result
                and "documents" in content_result
                and isinstance(content_result["documents"], list)
            ):
                logger.info(
                    f"Successfully parsed {len(content_result['documents'])} document chunks from '{file.filename}'."
                )
                return content_result["documents"]
            else:
                logger.warning(
                    f"Parsing result for '{file.filename}' missing 'documents' list or has wrong format. Result: {content_result}"
                )
                return (
                    None  # Return None or empty list if parsing fails or yields no docs
                )

        except Exception as e:
            logger.exception(
                f"Error parsing file content for '{file.filename}' (type: {file_type}): {e}",
                exc_info=True,
            )
            return None  # Return None on parsing error

    async def _parse_website_content(
        self, source: str, urls: List[str], api_key: str
    ) -> Optional[List[Dict]]:
        """Parses website content using LyzrParse."""
        logger.info(f"Parsing website content for source: '{source}', URLs: {urls}")
        try:
            content_result = await self.parse.parse_website(api_key, source, urls)
            if (
                content_result
                and "documents" in content_result
                and isinstance(content_result["documents"], list)
            ):
                logger.info(
                    f"Successfully parsed {len(content_result['documents'])} document chunks from website source '{source}'."
                )
                return content_result["documents"]
            else:
                logger.warning(
                    f"Parsing result for website '{source}' missing 'documents' list or has wrong format. Result: {content_result}"
                )
                return None
        except Exception as e:
            logger.exception(
                f"Error parsing website content for source '{source}': {e}",
                exc_info=True,
            )
            return None

    async def upload_file(
        self, kb_id: str, file: UploadFile, api_key: str
    ) -> Optional[KnowledgeBaseModel]:
        """Uploads a single file: Detects type, parses, stores in RAG, S3, and DB."""
        if not file or not file.filename:
            logger.error("upload_file called with invalid file object.")
            return None

        logger.info(
            f"Starting upload process for file '{file.filename}' to KB ID: {kb_id}"
        )
        file_type = self._determine_file_type(file)
        if (
            file_type == "unknown" or file_type not in DATA_PARSERS
        ):  # Check if we support parsing this type
            logger.error(
                f"Unsupported or unknown file type '{file_type}' for file '{file.filename}'. Upload aborted."
            )
            raise ValueError(
                f"Unsupported file type: {file_type}"
            )  # Raise error to caller

        uploaded_doc_record: Optional[KnowledgeBaseModel] = None
        s3_location: Optional[str] = None

        try:
            # 1. Parse the file content
            parsed_content = await self._parse_file_content(file_type, file, api_key)
            if (
                parsed_content is None
            ):  # Check if parsing failed or returned no documents
                raise Exception(
                    f"Parsing failed or returned no content for file '{file.filename}'."
                )

            # 2. Upload parsed content to RAG store
            logger.info(
                f"Storing {len(parsed_content)} parsed chunks from '{file.filename}' into RAG store (KB ID: {kb_id})..."
            )
            rag_result = await self.rag.store_document(kb_id, parsed_content, api_key)
            # TODO: Replace with actual check based on rag_result structure
            if not rag_result or rag_result.get("status") != "success":  # Example check
                logger.warning(
                    f"RAG store result indicates potential failure for '{file.filename}'. Result: {rag_result}"
                )
                # Decide whether to proceed if RAG store fails - maybe proceed but log warning?

            # 3. Upload original file to S3
            logger.info(
                f"Uploading original file '{file.filename}' to S3 bucket for KB ID: {kb_id}..."
            )
            # Ensure file pointer is at the beginning before S3 upload
            file.file.seek(0)
            s3_location = self.s3.upload_file(
                file, f"{kb_id}/{file.filename}"
            )  # Assuming upload_file returns URL or path string
            if not s3_location:
                logger.warning(
                    f"S3 upload failed or returned no location for '{file.filename}'. Proceeding without S3 link."
                )
                s3_location = (
                    ""  # Store empty string if S3 fails but we want to proceed
                )

            logger.info(f"File '{file.filename}' uploaded to S3: {s3_location}")

            # 4. Create database record
            # Map string file_type to KbFileType Enum
            doc_type_map = {
                "pdf": KbFileType.PDF,
                "docx": KbFileType.DOCX,
                "txt": KbFileType.TXT,
                "csv": KbFileType.CSV,
                "doc": KbFileType.WEBSITE,
            }
            doc_type_enum = doc_type_map.get(file_type, None)  # Default to UNKNOWN

            kb_entry_data = {
                "name": file.filename,
                "doc_type": doc_type_enum,
                "doc_link": str(s3_location),
                "kb_id": kb_id,
            }
            logger.info(
                f"Creating database record for uploaded file '{file.filename}' in KB ID: {kb_id}..."
            )
            uploaded_doc_record = await self.db.kb_repository.create(kb_entry_data)
            logger.info(
                f"Successfully created DB record (ID: {uploaded_doc_record.id}) for file '{file.filename}'."
            )

            return uploaded_doc_record

        except Exception as e:
            logger.exception(
                f"Upload failed for file '{file.filename}' to KB {kb_id}: {e}",
                exc_info=True,
            )
            # Consider cleanup steps here if needed (e.g., delete from RAG/S3 if DB entry fails?)
            return None  # Indicate failure

    async def upload_files(
        self, kb_id: str, files: List[UploadFile], api_key: str
    ) -> List[KnowledgeBaseModel]:
        """Uploads multiple files concurrently."""
        if not files:
            logger.info("upload_files called with empty file list.")
            return []

        logger.info(f"Starting batch upload of {len(files)} files to KB ID: {kb_id}")
        tasks = [
            asyncio.create_task(
                self.upload_file(kb_id, file, api_key), name=f"Upload-{file.filename}"
            )
            for file in files
            if file and file.filename  # Basic validation
        ]

        # Run tasks concurrently and capture results/exceptions
        results = await asyncio.gather(*tasks, return_exceptions=True)

        uploaded_docs: List[KnowledgeBaseModel] = []
        failed_uploads = 0
        for i, result in enumerate(results):
            original_filename = (
                files[i].filename if i < len(files) else "unknown"
            )  # Get corresponding filename
            if isinstance(result, Exception):
                logger.error(
                    f"Batch upload failed for file '{original_filename}': {result}",
                    exc_info=False,
                )  # Don't log full trace again if already logged in upload_file
                failed_uploads += 1
            elif isinstance(
                result, KnowledgeBaseModel
            ):  # Check if it's the expected successful return type
                uploaded_docs.append(result)
            elif (
                result is None
            ):  # Handle case where upload_file returned None indicating failure
                logger.error(
                    f"Batch upload failed for file '{original_filename}' (returned None)."
                )
                failed_uploads += 1
            else:  # Unexpected return type
                logger.error(
                    f"Batch upload for file '{original_filename}' returned unexpected type: {type(result)}"
                )
                failed_uploads += 1

        logger.info(
            f"Batch upload completed for KB ID: {kb_id}. Successful: {len(uploaded_docs)}, Failed: {failed_uploads}"
        )
        return uploaded_docs  # Return list of successfully created DB records

    async def upload_website_data(
        self, kb_id: str, source: str, urls: List[str], api_key: str
    ) -> Optional[KnowledgeBaseModel]:
        """Parses website data, stores in RAG, and creates a DB record."""
        logger.info(
            f"Starting website data upload for source '{source}' to KB ID: {kb_id}"
        )
        try:
            # 1. Parse website content
            parsed_content = await self._parse_website_content(source, urls, api_key)
            if parsed_content is None:
                raise Exception(
                    f"Parsing failed or returned no content for website source '{source}'."
                )

            # 2. Store parsed content in RAG
            logger.info(
                f"Storing {len(parsed_content)} parsed chunks from '{source}' into RAG store (KB ID: {kb_id})..."
            )
            rag_result = await self.rag.store_document(kb_id, parsed_content, api_key)
            if not rag_result or rag_result.get("status") != "success":  # Example check
                logger.warning(
                    f"RAG store result indicates potential failure for '{source}'. Result: {rag_result}"
                )

            # 3. Create database record
            kb_entry_data = {
                "name": source,  # Use source name (e.g., domain) as the name
                "doc_type": KbFileType.WEBSITE,
                "doc_link": (
                    urls[0] if urls else ""
                ),  # Store first URL as reference link? Or joined list?
                "kb_id": kb_id,
            }
            logger.info(
                f"Creating database record for website source '{source}' in KB ID: {kb_id}..."
            )
            uploaded_doc_record = await self.db.kb_repository.create(kb_entry_data)
            logger.info(
                f"Successfully created DB record (ID: {uploaded_doc_record.id}) for website source '{source}'."
            )

            return uploaded_doc_record

        except Exception as e:
            logger.exception(
                f"Upload failed for website source '{source}' to KB {kb_id}: {e}",
                exc_info=True,
            )
            return None

    async def upload_text_data(
        self, kb_id: str, name: str, text: str, api_key: str
    ) -> Optional[KnowledgeBaseModel]:
        """Parses raw text, stores in RAG, and creates a DB record."""
        # Added 'name' parameter for better identification than just truncated text
        if not text:
            logger.warning("upload_text_data called with empty text.")
            return None
        logger.info(f"Starting text data upload for name '{name}' to KB ID: {kb_id}")
        try:
            # 1. Parse text content
            # Using provided name as the source identifier
            content_to_parse = [RawTextType(source=name, text=text)]
            parsed_content_result = await self.parse.parse_text(
                content_to_parse, api_key
            )
            if (
                not parsed_content_result
                or "documents" not in parsed_content_result
                or not isinstance(parsed_content_result["documents"], list)
            ):
                raise Exception(
                    f"Parsing failed or returned invalid format for text '{name}'."
                )
            parsed_content = parsed_content_result["documents"]
            if not parsed_content:
                raise Exception(
                    f"Parsing returned no document chunks for text '{name}'."
                )

            # 2. Store parsed content in RAG
            logger.info(
                f"Storing {len(parsed_content)} parsed chunks from text '{name}' into RAG store (KB ID: {kb_id})..."
            )
            rag_result = await self.rag.store_document(kb_id, parsed_content, api_key)
            if not rag_result or rag_result.get("status") != "success":  # Example check
                logger.warning(
                    f"RAG store result indicates potential failure for text '{name}'. Result: {rag_result}"
                )

            # 3. Create database record
            kb_entry_data = {
                "name": name,  # Use the provided name
                "doc_type": KbFileType.TEXT,
                "doc_link": "",  # No external link for raw text
                "kb_id": kb_id,
            }
            logger.info(
                f"Creating database record for text '{name}' in KB ID: {kb_id}..."
            )
            uploaded_doc_record = await self.db.kb_repository.create(kb_entry_data)
            logger.info(
                f"Successfully created DB record (ID: {uploaded_doc_record.id}) for text '{name}'."
            )

            return uploaded_doc_record

        except Exception as e:
            logger.exception(
                f"Upload failed for text '{name}' to KB {kb_id}: {e}", exc_info=True
            )
            return None

    async def delete_kb_documents(
        self, kb_id: str, sources: List[str], api_key: str
    ) -> int:
        """Deletes documents from RAG store and corresponding DB entries by source name."""
        if not sources:
            logger.warning("delete_kb_documents called with empty sources list.")
            return 0
        logger.info(
            f"Attempting to delete {len(sources)} sources from KB ID: {kb_id}. Sources: {sources}"
        )
        deleted_db_count = 0
        try:
            # 1. Delete from RAG store first
            # Assuming delete_rag_documents handles errors internally or raises
            logger.debug(f"Calling RAG API to delete sources for KB ID {kb_id}...")
            rag_result = await self.rag.delete_rag_documents(kb_id, sources, api_key)
            # TODO: Check rag_result structure to confirm success/get count if available
            logger.info(
                f"RAG API delete call completed for sources in KB ID {kb_id}. Result: {rag_result}"
            )  # Log result

            # 2. Delete corresponding entries from our DB
            # Assuming delete_docs takes kb_id and list of names (sources)
            logger.debug(
                f"Deleting corresponding DB entries for sources in KB ID {kb_id}..."
            )
            deleted_db_count = await self.db.kb_repository.delete_docs(kb_id, sources)
            logger.info(
                f"Deleted {deleted_db_count} document entries from database for KB ID {kb_id}."
            )

            return deleted_db_count  # Return DB count as confirmation

        except Exception as e:
            logger.exception(
                f"Error deleting documents from KB {kb_id} for sources {sources}: {e}",
                exc_info=True,
            )
            # Depending on requirements, you might return partial success or raise
            raise Exception(
                f"Failed to complete deletion for KB {kb_id}: {e}"
            ) from e  # Re-raise

    async def get_kb_documents(
        self, kb_id: str, search_string: str = ""
    ) -> List[KnowledgeBaseModel]:
        """Retrieves all document records for a KB, optionally filtered by name."""
        logger.info(
            f"Retrieving documents for KB ID: {kb_id}, Search: '{search_string}'"
        )
        try:
            # Assuming get_all retrieves all metadata records for the kb_id
            all_documents = await self.db.kb_repository.get_all(kb_id)
            logger.debug(
                f"Retrieved {len(all_documents)} total documents for KB ID: {kb_id}"
            )

            if search_string:
                search_lower = search_string.lower()
                # Perform case-insensitive filtering in memory
                filtered_documents = [
                    doc for doc in all_documents if search_lower in doc.name.lower()
                ]
                logger.info(
                    f"Filtered documents by '{search_string}', {len(filtered_documents)} results."
                )
                return filtered_documents
            else:
                return all_documents
        except RepositoryReadException as e:
            # Handle case where the KB itself might not be found or DB error
            logger.error(
                f"Failed to read documents for KB ID {kb_id}: {e}", exc_info=True
            )
            return []  # Return empty list on read error
        except Exception as e:
            logger.exception(
                f"Unexpected error retrieving documents for KB {kb_id}: {e}",
                exc_info=True,
            )
            return []

    async def create_new_kb(
        self, config_data: LyzrRagConfig, api_key: str
    ) -> LyzrRagConfig:
        """Creates a new RAG configuration (Knowledge Base) via the API."""
        logger.info(
            f"Attempting to create new KB with description: '{config_data.get('description', 'N/A')}'"
        )
        # Log config carefully, potentially masking sensitive parts if any exist in LyzrRagConfig
        logger.debug(f"KB Config Data: {config_data}")
        try:
            # Call the RAG API to create the configuration
            new_kb_config = await self.rag.create_rag_config(config_data, api_key)
            # The returned object should ideally include the new KB ID ('id' field in LyzrRagConfig)
            if not new_kb_config or not new_kb_config.get("id"):
                logger.error(
                    f"KB creation call succeeded but response missing ID. Response: {new_kb_config}"
                )
                raise Exception(
                    "KB created, but failed to retrieve its ID from the API response."
                )

            logger.info(f"Successfully created new KB with ID: {new_kb_config['id']}")
            return new_kb_config  # Return the full config, including the new ID
        except Exception as e:
            logger.exception(f"Failed to create new KB: {e}", exc_info=True)
            raise Exception(f"Could not create Knowledge Base: {e}") from e

    async def retrieve_relevant_data(
        self, kb_id: str, query: str, api_key: str
    ) -> List[Dict]:
        """Retrieves relevant document chunks from the RAG store for a given query."""
        logger.info(
            f"Retrieving relevant data from KB ID: {kb_id} for query: '{query[:100]}...'"
        )
        try:
            # Call the RAG API to query documents
            documents = await self.rag.query_rag_documents(kb_id, query, api_key)
            count = len(documents) if isinstance(documents, list) else 0
            logger.info(
                f"Retrieved {count} relevant document chunks for KB ID: {kb_id}."
            )
            # Ensure return is always a list
            return documents if isinstance(documents, list) else []
        except Exception as e:
            logger.exception(
                f"Failed to retrieve relevant data for KB {kb_id}: {e}", exc_info=True
            )
            # Return empty list on failure or re-raise? Returning empty list for now.
            return []

import logging
from typing import Any, Dict

from lib.models.topic_models import TopicModel, TopicsPaginatedResponse
from lib.knowledge_base import (
    KnowledgeBase,
)
from lib.repositories.exceptions import (
    RepositoryCreateException,
    RepositoryNotFoundException,
    RepositoryReadException,
    RepositoryUpdateException,
    RepositoryDeleteException,
)

from lib.repositories.repository_manager_protocol import RepositoryManagerProtocol
from lib.user import UserService
from lib.content_desk import ContentDesk

logger = logging.getLogger(__name__)


class Topic:
    """
    Service class for managing Topics.
    Orchestrates interactions between repositories, knowledge base service, and user service.
    """

    def __init__(
        self,
        db: RepositoryManagerProtocol,
        kb: KnowledgeBase,
        user: UserService,
        content_desk: ContentDesk,
    ):
        """
        Initializes the Topic service.

        Args:
            db (RepositoryManagerProtocol): Provides access to data repositories (e.g., topic_repository).
            kb (KnowledgeBase): Service for interacting with the knowledge base system.
            user (UserService): Service for retrieving user information.
        """
        self.db = db
        self.kb = kb
        self.content_desk = content_desk
        self.user = user
        logger.info("Topic service initialized.")

    async def create(self, topic: TopicModel) -> TopicModel:
        """
        Creates a new topic, including setting up an associated knowledge base.

        Args:
            topic (TopicModel): The topic data to create. Must include user_id and topic name.

        Returns:
            TopicModel: The fully created topic object, including its generated kb_id.

        Raises:
            Exception: A user-friendly error if topic creation fails at any step.
        """
        logger.info(
            f"Attempting to create topic '{topic.topic}' for user {topic.user_id}"
        )
        try:
            # 1. Fetch user data (needed for API key)
            logger.debug(f"Fetching user data for user_id: {topic.user_id}")
            user_data = await self.user.get_user_by_id(topic.user_id)
            if not user_data:
                # Handle case where user service returns None or raises an error implicitly
                logger.error(
                    f"User not found with id: {topic.user_id} during topic creation."
                )
                raise Exception(f"Cannot create topic: User {topic.user_id} not found.")

            # 2. Prepare KB configuration and create the KB entry
            """
            logger.debug(f"Preparing default KB config for topic: {topic.topic}")
            config = self.kb.get_default_config(topic.topic, topic.user_id)
            logger.debug(f"Creating new knowledge base entry for topic: {topic.topic}")
            kb_entry = await self.kb.create_new_kb(config, user_data.api_key)
            topic.kb_id = kb_entry["id"]
            logger.info(
                f"Knowledge base created with id: {kb_entry['id']} for topic: {topic.topic}"
            )
            """

            # 3. Create Empty Content Desk
            logger.info("Creating empty content desk")
            desk = await self.content_desk.create_empty_desk(
                topic.topic, topic.context, "", ""
            )
            topic.desk_id = desk.id

            # 4. Create the topic entry in the repository
            logger.debug(f"Creating topic entry in repository for topic: {topic.topic}")
            created_topic = await self.db.topic_repository.create(topic)
            logger.info(f"Successfully created topic with id: {created_topic.id}")
            return created_topic
        except RepositoryCreateException as e:
            logger.error(
                f"Repository error during topic creation for user {topic.user_id}: {e}",
                exc_info=True,
            )
            raise Exception(
                "Cannot create topic at the moment due to a storage issue, please try again."
            )
        except Exception as e:
            logger.error(
                f"Unexpected error during topic creation for user {topic.user_id}: {e}",
                exc_info=True,
            )
            raise Exception("An unexpected error occurred while creating the topic.")

    async def get(self, topic_id: str) -> TopicModel:
        """
        Retrieves a specific topic by its ID.

        Args:
            topic_id (str): The unique identifier of the topic to retrieve.

        Returns:
            TopicModel: The found topic object.

        Raises:
            Exception: A user-friendly error if the topic is not found or retrieval fails.
        """
        logger.info(f"Attempting to retrieve topic with id: {topic_id}")
        try:
            topic = await self.db.topic_repository.get(topic_id)
            logger.info(f"Successfully retrieved topic with id: {topic_id}")
            return topic
        except RepositoryNotFoundException as e:
            logger.warning(f"Topic not found with id {topic_id}: {e}")
            raise Exception(f"Cannot find a topic with id {topic_id}")
        except RepositoryReadException as e:
            logger.error(
                f"Repository read error when retrieving topic {topic_id}: {e}",
                exc_info=True,
            )
            raise Exception(f"Something went wrong when looking for topic: {topic_id}")
        except Exception as e:
            logger.error(
                f"Unexpected error retrieving topic {topic_id}: {e}", exc_info=True
            )
            raise Exception("An unexpected error occurred while retrieving the topic.")

    async def get_user_topics(
        self, user_id: str, page_size: int, page_no: int
    ) -> TopicsPaginatedResponse:
        """
        Retrieves a paginated list of topics belonging to a specific user.

        Args:
            user_id (str): The ID of the user whose topics are to be retrieved.
            page_size (int): The maximum number of topics to return per page.
            page_no (int): The page number to retrieve (1-based index).

        Returns:
            TopicsPaginatedResponse: An object containing the list of topics for the page
                                     and pagination metadata.

        Raises:
            Exception: A user-friendly error if topics cannot be retrieved.
        """
        logger.info(
            f"Attempting to retrieve topics for user {user_id}, page: {page_no}, size: {page_size}"
        )
        if page_no < 1:
            page_no = 1
            logger.debug("Adjusted page number to 1 as it was less than 1.")
        if page_size < 1:
            page_size = 10  # Or a default value
            logger.debug(
                f"Adjusted page size to default ({page_size}) as it was less than 1."
            )

        try:
            skip = (page_no - 1) * page_size
            query = {"user_id": user_id}

            # Get total count for pagination metadata
            logger.debug(f"Fetching total topic count for user {user_id}")
            # This assumes topic_repository has a method get_total_count
            total_count = await self.db.topic_repository.get_total_count(query)
            logger.debug(f"Total topics found for user {user_id}: {total_count}")

            # Get the topics for the current page
            logger.debug(
                f"Fetching topics for user {user_id} with skip: {skip}, limit: {page_size}"
            )
            # This assumes topic_repository.get_where supports skip and limit parameters
            topics = await self.db.topic_repository.get_where(
                query, skip=skip, limit=page_size
            )
            logger.info(
                f"Successfully retrieved {len(topics)} topics for user {user_id} on page {page_no}"
            )

            return TopicsPaginatedResponse(
                items=topics,
                total_items=total_count,
                page_no=page_no,
                page_size=page_size,
            )
        except RepositoryReadException as e:
            logger.error(
                f"Repository read error when retrieving topics for user {user_id}: {e}",
                exc_info=True,
            )
            raise Exception(
                "Something went wrong when looking for your topics. Please try again."
            )
        except Exception as e:
            logger.error(
                f"Unexpected error retrieving topics for user {user_id}: {e}",
                exc_info=True,
            )
            raise Exception("An unexpected error occurred while retrieving topics.")

    async def update(self, topic_id: str, update_data: Dict[str, Any]) -> TopicModel:
        """
        Updates an existing topic identified by its ID.

        Args:
            topic_id (str): The unique identifier of the topic to update.
            update_data (Dict[str, Any]): A dictionary containing the fields to update.
                                          Should not contain 'topic_id', 'user_id', or 'kb_id'.

        Returns:
            TopicModel: The updated topic object.

        Raises:
            Exception: A user-friendly error if the update fails or the topic is not found.
        """
        logger.info(f"Attempting to update topic with id: {topic_id}")
        # Prevent modification of critical identifiers via this method
        update_data.pop("user_id", None)
        update_data.pop("kb_id", None)
        update_data.pop("_id", None)  # Also prevent direct _id modification
        update_data.pop("created_at", None)  # Usually should not be updated manually

        if not update_data:
            logger.warning(
                f"Update called for topic {topic_id} with no valid fields to update."
            )
            # Option 1: Raise an error
            # raise ValueError("No valid fields provided for topic update.")
            # Option 2: Return the existing topic without changes (requires fetching it first)
            # Option 3: Return None or indicate no change (less ideal)
            # Let's fetch and return for now, assuming no-op is acceptable if no data given
            return await self.get(topic_id)

        try:
            logger.debug(
                f"Calling repository update for topic {topic_id} with data: {update_data.keys()}"
            )
            # This assumes topic_repository has an update method
            updated_topic = await self.db.topic_repository.update(topic_id, update_data)
            logger.info(f"Successfully updated topic with id: {topic_id}")
            return updated_topic
        except RepositoryNotFoundException as e:
            logger.warning(f"Topic not found for update with id {topic_id}: {e}")
            raise Exception(f"Cannot update: Topic with id {topic_id} not found.")
        except RepositoryUpdateException as e:
            logger.error(
                f"Repository update error for topic {topic_id}: {e}", exc_info=True
            )
            raise Exception(
                f"Failed to update topic {topic_id} due to a storage issue."
            )
        except Exception as e:
            logger.error(
                f"Unexpected error updating topic {topic_id}: {e}", exc_info=True
            )
            raise Exception("An unexpected error occurred while updating the topic.")

    async def delete(self, topic_id: str) -> TopicModel:
        """
        Deletes a topic identified by its ID.

        Note: This currently only deletes the topic record. Associated KB cleanup
              might need to be handled separately or integrated here if required.

        Args:
            topic_id (str): The unique identifier of the topic to delete.

        Returns:
            TopicModel: The topic object that was deleted.

        Raises:
            Exception: A user-friendly error if deletion fails or the topic is not found.
        """
        logger.info(f"Attempting to delete topic with id: {topic_id}")
        try:
            # Fetch the topic first if we need its data (e.g., kb_id for cleanup)
            # topic_to_delete = await self.get(topic_id) # Use internal get for potential data need
            # kb_id_to_cleanup = topic_to_delete.kb_id

            # Call repository delete
            logger.debug(f"Calling repository delete for topic {topic_id}")
            # This assumes topic_repository has a delete method returning the deleted doc
            deleted_topic = await self.db.topic_repository.delete(topic_id)

            # Placeholder for potential KB cleanup logic:
            # if kb_id_to_cleanup:
            #    logger.info(f"Attempting to cleanup associated KB {kb_id_to_cleanup} for deleted topic {topic_id}")
            #    try:
            #        # Assuming user info might be needed for KB deletion API key? Fetch if necessary.
            #        user_data = await self.user.get_user_by_id(deleted_topic.user_id)
            #        await self.kb.delete_kb(kb_id_to_cleanup, user_data.api_key)
            #        logger.info(f"Successfully cleaned up KB {kb_id_to_cleanup}")
            #    except Exception as kb_del_err:
            #        logger.error(f"Failed to cleanup KB {kb_id_to_cleanup} for deleted topic {topic_id}: {kb_del_err}", exc_info=True)
            #        # Decide if this error should prevent successful response - likely not, log and continue.

            logger.info(f"Successfully deleted topic with id: {topic_id}")
            return deleted_topic  # Return the data of the object that was deleted
        except RepositoryNotFoundException as e:
            logger.warning(f"Topic not found for deletion with id {topic_id}: {e}")
            raise Exception(f"Cannot delete: Topic with id {topic_id} not found.")
        except RepositoryDeleteException as e:
            logger.error(
                f"Repository delete error for topic {topic_id}: {e}", exc_info=True
            )
            raise Exception(
                f"Failed to delete topic {topic_id} due to a storage issue."
            )
        except Exception as e:
            # This will also catch RepositoryNotFoundException if self.get() is used above and fails
            logger.error(
                f"Unexpected error deleting topic {topic_id}: {e}", exc_info=True
            )
            raise Exception("An unexpected error occurred while deleting the topic.")

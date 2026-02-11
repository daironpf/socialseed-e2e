"""GraphQL Example - Simple Blog API.

This example demonstrates how to use the GraphQL testing capabilities
of socialseed-e2e to test a blog API with users, posts, and comments.

To run this example, you'll need a GraphQL server running at the specified endpoint.
For testing purposes, you can use any public GraphQL API or set up a local server.
"""

import logging
from typing import Any, Dict, Optional

from socialseed_e2e.core.base_graphql_page import BaseGraphQLPage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BlogGraphQLPage(BaseGraphQLPage):
    """Page class for testing a Blog GraphQL API.

    This class extends BaseGraphQLPage and provides convenient methods
    for common blog operations like creating users, posts, and comments.

    Example:
        >>> page = BlogGraphQLPage("https://api.example.com/graphql")
        >>> page.setup()
        >>>
        >>> # Create a user
        >>> result = page.create_user(name="John Doe", email="john@example.com")
        >>> user_id = page.get_data(result, "createUser.id")
        >>>
        >>> # Create a post
        >>> post = page.create_post(title="Hello", content="World", author_id=user_id)
        >>>
        >>> page.teardown()
    """

    def __init__(self, endpoint: str, **kwargs):
        """Initialize the Blog GraphQL page.

        Args:
            endpoint: GraphQL endpoint URL
            **kwargs: Additional arguments passed to BaseGraphQLPage
        """
        super().__init__(endpoint, **kwargs)

    def get_all_users(self) -> Dict[str, Any]:
        """Query all users from the API.

        Returns:
            GraphQL response with users data
        """
        query = """
        query GetAllUsers {
          users {
            id
            name
            email
            posts {
              id
              title
            }
          }
        }
        """
        return self.query(query)

    def get_user(self, user_id: str) -> Dict[str, Any]:
        """Query a specific user by ID.

        Args:
            user_id: User ID

        Returns:
            GraphQL response with user data
        """
        query = """
        query GetUser($id: ID!) {
          user(id: $id) {
            id
            name
            email
            posts {
              id
              title
              content
            }
          }
        }
        """
        return self.query(query, variables={"id": user_id})

    def create_user(self, name: str, email: str) -> Dict[str, Any]:
        """Create a new user.

        Args:
            name: User name
            email: User email

        Returns:
            GraphQL response with created user data
        """
        mutation = """
        mutation CreateUser($name: String!, $email: String!) {
          createUser(name: $name, email: $email) {
            id
            name
            email
            createdAt
          }
        }
        """
        return self.mutation(
            mutation,
            variables={"name": name, "email": email},
            operation_name="CreateUser",
        )

    def update_user(
        self, user_id: str, name: Optional[str] = None, email: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update an existing user.

        Args:
            user_id: User ID to update
            name: New name (optional)
            email: New email (optional)

        Returns:
            GraphQL response with updated user data
        """
        mutation = """
        mutation UpdateUser($id: ID!, $name: String, $email: String) {
          updateUser(id: $id, name: $name, email: $email) {
            id
            name
            email
            updatedAt
          }
        }
        """
        variables: Dict[str, Any] = {"id": user_id}
        if name:
            variables["name"] = name
        if email:
            variables["email"] = email

        return self.mutation(mutation, variables=variables, operation_name="UpdateUser")

    def delete_user(self, user_id: str) -> Dict[str, Any]:
        """Delete a user.

        Args:
            user_id: User ID to delete

        Returns:
            GraphQL response with deletion result
        """
        mutation = """
        mutation DeleteUser($id: ID!) {
          deleteUser(id: $id) {
            success
            message
          }
        }
        """
        return self.mutation(
            mutation,
            variables={"id": user_id},
            operation_name="DeleteUser",
        )

    def get_all_posts(self) -> Dict[str, Any]:
        """Query all posts from the API.

        Returns:
            GraphQL response with posts data
        """
        query = """
        query GetAllPosts {
          posts {
            id
            title
            content
            author {
              id
              name
            }
            comments {
              id
              content
            }
          }
        }
        """
        return self.query(query)

    def get_post(self, post_id: str) -> Dict[str, Any]:
        """Query a specific post by ID.

        Args:
            post_id: Post ID

        Returns:
            GraphQL response with post data
        """
        query = """
        query GetPost($id: ID!) {
          post(id: $id) {
            id
            title
            content
            author {
              id
              name
              email
            }
            comments {
              id
              content
              author {
                name
              }
            }
          }
        }
        """
        return self.query(query, variables={"id": post_id})

    def create_post(self, title: str, content: str, author_id: str) -> Dict[str, Any]:
        """Create a new post.

        Args:
            title: Post title
            content: Post content
            author_id: Author user ID

        Returns:
            GraphQL response with created post data
        """
        mutation = """
        mutation CreatePost($title: String!, $content: String!, $authorId: ID!) {
          createPost(title: $title, content: $content, authorId: $authorId) {
            id
            title
            content
            createdAt
            author {
              id
              name
            }
          }
        }
        """
        return self.mutation(
            mutation,
            variables={"title": title, "content": content, "authorId": author_id},
            operation_name="CreatePost",
        )

    def update_post(
        self, post_id: str, title: Optional[str] = None, content: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update an existing post.

        Args:
            post_id: Post ID to update
            title: New title (optional)
            content: New content (optional)

        Returns:
            GraphQL response with updated post data
        """
        mutation = """
        mutation UpdatePost($id: ID!, $title: String, $content: String) {
          updatePost(id: $id, title: $title, content: $content) {
            id
            title
            content
            updatedAt
          }
        }
        """
        variables: Dict[str, Any] = {"id": post_id}
        if title:
            variables["title"] = title
        if content:
            variables["content"] = content

        return self.mutation(mutation, variables=variables, operation_name="UpdatePost")

    def delete_post(self, post_id: str) -> Dict[str, Any]:
        """Delete a post.

        Args:
            post_id: Post ID to delete

        Returns:
            GraphQL response with deletion result
        """
        mutation = """
        mutation DeletePost($id: ID!) {
          deletePost(id: $id) {
            success
            message
          }
        }
        """
        return self.mutation(
            mutation,
            variables={"id": post_id},
            operation_name="DeletePost",
        )

    def add_comment(self, post_id: str, content: str, author_id: str) -> Dict[str, Any]:
        """Add a comment to a post.

        Args:
            post_id: Post ID
            content: Comment content
            author_id: Author user ID

        Returns:
            GraphQL response with created comment data
        """
        mutation = """
        mutation AddComment($postId: ID!, $content: String!, $authorId: ID!) {
          addComment(postId: $postId, content: $content, authorId: $authorId) {
            id
            content
            createdAt
            author {
              id
              name
            }
          }
        }
        """
        return self.mutation(
            mutation,
            variables={"postId": post_id, "content": content, "authorId": author_id},
            operation_name="AddComment",
        )


def example_using_query_builder():
    """Example using the GraphQLQueryBuilder for dynamic queries."""
    print("\n=== Example: Using GraphQLQueryBuilder ===\n")

    # Create a page instance
    page = BlogGraphQLPage("https://api.example.com/graphql")

    # Get a query builder
    builder = page.builder()

    # Build a complex query with nested fields
    query = (
        builder.query("GetUserWithPosts")
        .variable("id", "ID!")
        .field("user", id="$id")
        .fields("id", "name", "email")
        .subfield("posts")
        .fields("id", "title", "content")
        .end_field()
        .build()
    )

    print("Generated Query:")
    print(query)
    print()

    # Example with fragments
    builder2 = page.builder()
    query2 = (
        builder2.query("GetAllUsers")
        .fragment("UserFields", "User", "id", "name", "email")
        .field("users")
        .subfield("...UserFields")
        .end_field()
        .build()
    )

    print("Query with Fragments:")
    print(query2)


def example_using_introspection():
    """Example using GraphQL introspection."""
    print("\n=== Example: Using GraphQL Introspection ===\n")

    page = BlogGraphQLPage("https://api.example.com/graphql")
    page.setup()

    try:
        introspector = page.introspector()

        # Get all available queries
        print("Available Queries:")
        queries = introspector.get_queries()
        for q in queries:
            print(f"  - {q['name']}: {q.get('description', 'No description')}")

        # Get all available mutations
        print("\nAvailable Mutations:")
        mutations = introspector.get_mutations()
        for m in mutations:
            print(f"  - {m['name']}: {m.get('description', 'No description')}")

        # Get specific type information
        user_type = introspector.get_type("User")
        if user_type:
            print("\nUser Type Fields:")
            for field in user_type.get("fields", []):
                print(f"  - {field['name']}: {field['type']['name']}")

    finally:
        page.teardown()


def example_simple_query():
    """Example of a simple GraphQL query using the convenience function."""
    print("\n=== Example: Simple Query Function ===\n")

    from socialseed_e2e.core.base_graphql_page import graphql_query

    # Execute a simple query without creating a page instance
    result = graphql_query(
        "https://api.example.com/graphql",
        "{ __typename }",
    )

    print("Result:", result)


def example_full_workflow():
    """Example of a complete testing workflow."""
    print("\n=== Example: Full Testing Workflow ===\n")

    page = BlogGraphQLPage("https://api.example.com/graphql")
    page.setup()

    try:
        # 1. Create a user
        print("1. Creating user...")
        result = page.create_user("John Doe", "john@example.com")
        page.assert_no_errors(result)
        user_id = page.get_data(result, "createUser.id")
        print(f"   Created user with ID: {user_id}")

        # 2. Query the user back
        print("2. Querying user...")
        result = page.get_user(user_id)
        page.assert_no_errors(result)
        user_name = page.get_data(result, "user.name")
        print(f"   User name: {user_name}")

        # 3. Create a post
        print("3. Creating post...")
        result = page.create_post("Hello GraphQL", "This is my first post!", user_id)
        page.assert_no_errors(result)
        post_id = page.get_data(result, "createPost.id")
        print(f"   Created post with ID: {post_id}")

        # 4. Query all posts
        print("4. Querying all posts...")
        result = page.get_all_posts()
        page.assert_no_errors(result)
        posts = page.get_data(result, "posts")
        print(f"   Total posts: {len(posts) if posts else 0}")

        # 5. Add a comment
        print("5. Adding comment...")
        result = page.add_comment(post_id, "Great post!", user_id)
        page.assert_no_errors(result)
        print("   Comment added successfully")

        # 6. Delete the post
        print("6. Deleting post...")
        result = page.delete_post(post_id)
        page.assert_no_errors(result)
        print("   Post deleted successfully")

        # 7. Delete the user
        print("7. Deleting user...")
        result = page.delete_user(user_id)
        page.assert_no_errors(result)
        print("   User deleted successfully")

        print("\n✓ All operations completed successfully!")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        raise

    finally:
        page.teardown()


def example_error_handling():
    """Example of error handling."""
    print("\n=== Example: Error Handling ===\n")

    page = BlogGraphQLPage("https://api.example.com/graphql")
    page.setup()

    try:
        # Try to get a non-existent user
        result = page.get_user("non-existent-id")

        # Check for errors manually
        errors = page.get_errors(result)
        if errors:
            print(f"Expected error occurred: {errors[0]['message']}")
        else:
            data = page.get_data(result, "user")
            if data is None:
                print("User not found (null response)")

        # Using assert_no_errors (would raise GraphQLError if errors exist)
        # page.assert_no_errors(result)

    finally:
        page.teardown()


if __name__ == "__main__":
    # Run examples (note: these require a running GraphQL server)

    print("=" * 60)
    print("GraphQL Testing Examples")
    print("=" * 60)

    # These examples generate queries without making actual requests
    example_using_query_builder()

    # These examples would require a running server
    # Uncomment to run against a real GraphQL API:
    # example_simple_query()
    # example_using_introspection()
    # example_full_workflow()
    # example_error_handling()

    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)
    print("\nNote: Most examples require a running GraphQL server.")
    print("Uncomment the function calls in __main__ to run live examples.")

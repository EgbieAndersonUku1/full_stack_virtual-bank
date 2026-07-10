class PendingCardRequestApplicationAlreadyExistsError(Exception):
    """
    Raised when a user attempts to create a new card request application
    while another application is still pending.

    Only one pending card request application is permitted per user.
    """
    pass
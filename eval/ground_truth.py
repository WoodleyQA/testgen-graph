GROUND_TRUTH = {
    "password_reset": {
        "requirement": "User can reset their password via a link emailed to their registered address. Reset links expire after 1 hour and can only be used once.",
        "cases": [
            {"id": "gt-1", "title": "Valid reset flow end to end", "category": "happy_path"},
            {"id": "gt-2", "title": "Request reset with unregistered email", "category": "negative"},
            {"id": "gt-3", "title": "New password fails complexity check", "category": "negative"},
            {"id": "gt-4", "title": "Reset link used after expiry window", "category": "boundary"},
            {"id": "gt-5", "title": "Reset link reused after already consumed", "category": "boundary"},
            {"id": "gt-6", "title": "Reused old/expired token rejected", "category": "auth_permission"},
            {"id": "gt-7", "title": "All existing sessions invalidated on successful reset", "category": "auth_permission"},
        ],
    },
    "file_upload": {
        "requirement": "User can upload a file up to 10MB, .pdf/.docx/.png only.",
        "cases": [
            {"id": "gt-1", "title": "Valid file within limits uploads successfully", "category": "happy_path"},
            {"id": "gt-2", "title": "Corrupt file with valid extension rejected", "category": "negative"},
            {"id": "gt-3", "title": "Disallowed extension rejected", "category": "negative"},
            {"id": "gt-4", "title": "File exactly at max size succeeds", "category": "boundary"},
            {"id": "gt-5", "title": "File 1 byte over max size rejected", "category": "boundary"},
            {"id": "gt-6", "title": "Zero-byte file rejected", "category": "boundary"},
            {"id": "gt-7", "title": "Upload attempted with expired session", "category": "auth_permission"},
            {"id": "gt-8", "title": "User cannot overwrite another user's file without permission", "category": "auth_permission"},
        ],
    },
    "search_filter": {
        "requirement": "User can filter search results by category, price range, and availability.",
        "cases": [
            {"id": "gt-1", "title": "Single valid filter narrows results correctly", "category": "happy_path"},
            {"id": "gt-2", "title": "Filter combination with no matches shows empty state", "category": "negative"},
            {"id": "gt-3", "title": "Malformed filter value handled gracefully", "category": "negative"},
            {"id": "gt-4", "title": "Maximum simultaneous filters still returns correctly", "category": "boundary"},
            {"id": "gt-5", "title": "Clearing all filters reverts to full result set", "category": "boundary"},
            {"id": "gt-6", "title": "Filter producing exactly one result displays correctly", "category": "boundary"},
            {"id": "gt-7", "title": "Restricted-content filter unavailable to unauthorized user", "category": "auth_permission"},
        ],
    },
    "subscription_cancel": {
        "requirement": "User can cancel their subscription; access continues until end of billing period.",
        "cases": [
            {"id": "gt-1", "title": "Active subscription cancels successfully", "category": "happy_path"},
            {"id": "gt-2", "title": "Cancelling an already-cancelled subscription is a no-op", "category": "negative"},
            {"id": "gt-3", "title": "Cancel attempted with outstanding failed payment", "category": "negative"},
            {"id": "gt-4", "title": "Cancellation on exact last day of billing cycle", "category": "boundary"},
            {"id": "gt-5", "title": "Re-subscribe before original cycle ends does not double-charge", "category": "boundary"},
            {"id": "gt-6", "title": "Non-owner cannot cancel shared account subscription", "category": "auth_permission"},
            {"id": "gt-7", "title": "Cancel attempted with stale/expired session token", "category": "auth_permission"},
        ],
    },
}

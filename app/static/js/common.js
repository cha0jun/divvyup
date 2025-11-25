// Fetch group members
async function fetchGroupMembers(group_id) {
    try {
        const response = await fetch(`/api/groups/${group_id}/members`, {
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        membersData = await response.json();
        return membersData;
    } catch (error) {
        console.error('Error fetching members:', error);
        throw error;
    }
}
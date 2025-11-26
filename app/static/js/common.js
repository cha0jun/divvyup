
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

async function fetchGroupDetails(group_id) {
    try {
        const response = await fetch(`/api/groups/${group_id}`, {
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            if (response.status === 404) {
                throw new Error('Group not found');
            } else if (response.status === 403) {
                throw new Error('You do not have permission to view this group');
            }
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        groupData = await response.json();
        return groupData;
    } catch (error) {
        console.error('Error fetching group details:', error);
        throw error;
    }
}

async function setupAdminPermissions(group_id, current_user_id) {
    const membersData = await fetchGroupMembers(group_id);
    const groupData = await fetchGroupDetails(group_id);
    const currentMember = membersData.find(m => m.user.id === current_user_id);
    const isAdmin = currentMember && currentMember.user.id === groupData.admin_id; 
    return isAdmin
}

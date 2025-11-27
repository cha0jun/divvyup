
// Global state
let groupData = null;
let membersData = null;
let balancesData = null;
let expensesData = null;
let currentMember = null;

// Helper function to escape HTML
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Format currency
function formatCurrency(amount) {
    return `$${parseFloat(amount).toFixed(2)}`;
}

// Format date
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

// Show/hide states
function showLoading() {
    document.getElementById('loadingState').style.display = 'block';
    document.getElementById('errorState').style.display = 'none';
    document.getElementById('mainContent').style.display = 'none';
}

function showError(message) {
    document.getElementById('loadingState').style.display = 'none';
    document.getElementById('errorState').style.display = 'block';
    document.getElementById('mainContent').style.display = 'none';
    document.getElementById('errorMessage').textContent = message;
}

function showContent() {
    document.getElementById('loadingState').style.display = 'none';
    document.getElementById('errorState').style.display = 'none';
    document.getElementById('mainContent').style.display = 'block';
}

// Fetch group details
async function fetchGroupDetails() {
    try {
        const response = await fetch(`/api/groups/${window.GROUP_ID}`, {
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

// Fetch group members
async function fetchGroupMembers() {
    try {
        const response = await fetch(`/api/groups/${window.GROUP_ID}/members`, {
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

// Fetch group balances
async function fetchGroupBalances() {
    try {
        const response = await fetch(`/api/groups/${window.GROUP_ID}/balances`, {
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        balancesData = await response.json();
        return balancesData;
    } catch (error) {
        console.error('Error fetching balances:', error);
        // Non-critical, just log the error
        return null;
    }
}

// Fetch recent expenses 
// async function fetchRecentExpenses() {
//     try {
//         const response = await fetch(`/api/groups/${window.GROUP_ID}/expenses?limit=3`, {
//             credentials: 'include',
//             headers: {
//                 'Content-Type': 'application/json'
//             }
//         });

//         if (!response.ok) {
//             throw new Error(`HTTP error! status: ${response.status}`);
//         }

//         expensesData = await response.json();
//         return expensesData;
//     } catch (error) {
//         console.error('Error fetching expenses:', error);
//         // Non-critical, just return empty array
//         return [];
//     }
// }

// Fetch Pending Invites ---
async function fetchPendingInvites() {
    try {
        const response = await fetch(`/api/groups/${window.GROUP_ID}/invitations`, {
            credentials: 'include',
        });

        // Handle 404 (Not Found) or 403 (Forbidden)
        if (response.status === 404 || response.status === 403) {
            console.log("No pending invites found or user not authorized to view them.");
            pendingInvitesData = []; // Set global data to empty
            return []; // Return empty array to Promise.all
        }

        // Handle other non-ok errors
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        pendingInvitesData = await response.json();
        return pendingInvitesData;

    } catch (error) {
        console.error('Error fetching pending invites:', error);
        pendingInvitesData = []; // Set global data to empty
        return []; // Return an empty array on any error
    }
}
// Display group info
function displayGroupInfo() {
    document.getElementById('groupName').textContent = groupData.name;
    document.getElementById('groupDescription').textContent = groupData.description || 'No description';
}

// Display members
function displayMembers() {
    const membersList = document.getElementById('membersList');

    if (!membersData || membersData.length === 0) {
        membersList.innerHTML = '<li class="list-group-item text-muted">No members yet.</li>';
        return;
    }

    // Find current member
    currentMember = membersData.find(m => m.user.id === window.CURRENT_USER);

    const membersHTML = membersData.map(member => {
        const isAdmin = member.user.id === groupData.admin_id;
        const isYou = window.CURRENT_USER && member.user.id === window.CURRENT_USER;

        return `
            <li class="list-group-item d-flex justify-content-between align-items-center">
                ${escapeHtml(member.user.name)}
                <div>
                    ${isAdmin ? '<span class="badge bg-primary">Admin</span>' : ''}
                    ${isYou ? '<span class="badge bg-info text-dark ms-2">You</span>' : ''}
                </div>
            </li>
        `;
    }).join('');

    membersList.innerHTML = membersHTML;
}

// Display balances
function displayBalances() {
    if (!balancesData || !currentMember) {
        console.warn("displayBalances: Data or currentMember not ready");
        return;
    }

    const currentUserName = currentMember.user.name;
    const currentUserBalance = balancesData.balances[currentUserName];

    if (currentUserBalance) {
        // 'owes' field is an OBJECT: {}
        // sum the values inside it to get the TOTAL number.

        const totalYouOwe = Object.values(currentUserBalance.owes).reduce(
            (sum, amount) => sum + amount, 0
        );

        const totalYouAreOwed = Object.values(currentUserBalance.owed_by).reduce(
            (sum, amount) => sum + amount, 0
        );

        const netBalance = currentUserBalance.net_balance;

        // --- update the HTML with three numbers ---
        document.getElementById('youAreOwed').textContent = formatCurrency(totalYouAreOwed);
        document.getElementById('youOwe').textContent = formatCurrency(totalYouOwe);

        const netBalanceEl = document.getElementById('netBalance');
        netBalanceEl.textContent = formatCurrency(Math.abs(netBalance));

        // Update color
        netBalanceEl.className = 'mb-0';
        if (netBalance > 0) {
            netBalanceEl.classList.add('text-success');
        } else if (netBalance < 0) {
            netBalanceEl.classList.add('text-danger');
        } else {
            netBalanceEl.classList.add('text-primary');
        }
    } else {
        console.warn(`No balance data found for user: ${currentUserName}`);
    }
}

function displayBalanceDetails() {
    if (!balancesData || !currentMember) {
        console.warn("displayBalanceDetails: Data or currentMember not ready");
        return;
    }

    const currentUserName = currentMember.user.name;
    const currentUserBalance = balancesData.balances[currentUserName];

    if (!currentUserBalance) {
        console.warn(`No balance data found for user: ${currentUserName}`);
        return;
    }
    const owedByList = document.getElementById('owedByList');
    const owedByEntries = Object.entries(currentUserBalance.owed_by);

    if (owedByEntries.length === 0) {
        owedByList.innerHTML = '<div class="text-muted small">No one owes you money</div>';
    } else {
        owedByList.innerHTML = owedByEntries
            .sort((a, b) => b[1] - a[1]) // Sort by amount descending
            .map(([name, amount]) => `
                        <div class="list-group-item d-flex justify-content-between align-items-center">
                            <span>${escapeHtml(name)}</span>
                            <span class="badge bg-primary rounded-pill">${formatCurrency(amount)}</span>
                        </div>
                    `).join('');
    }

    // Display who the current user owes
    const owesList = document.getElementById('owesList');
    const owesEntries = Object.entries(currentUserBalance.owes);

    if (owesEntries.length === 0) {
        owesList.innerHTML = '<div class="text-muted small">You don\'t owe anyone</div>';
    } else {
        owesList.innerHTML = owesEntries
            .sort((a, b) => b[1] - a[1]) // Sort by amount descending
            .map(([name, amount]) => `
                        <div class="list-group-item d-flex justify-content-between align-items-center">
                            <span>${escapeHtml(name)}</span>
                            <span class="badge bg-secondary rounded-pill">${formatCurrency(amount)}</span>
                        </div>
                    `).join('');
    }
}


// Display Pending Invites ---
function displayPendingInvites() {
    const invitesList = document.getElementById('pendingInvitesList');
    const invitesCountBadge = document.getElementById('pendingInvitesCount'); // Get the badge

    if (!pendingInvitesData || pendingInvitesData.length === 0) {
        invitesList.innerHTML = '<li class="list-group-item text-muted">No pending invitations.</li>';
        invitesCountBadge.textContent = '0'; // Set count to 0
        return;
    }

    // Update badge count
    invitesCountBadge.textContent = pendingInvitesData.length;

    invitesList.innerHTML = pendingInvitesData.map(inv => `
        <li class="list-group-item d-flex justify-content-between align-items-center" 
            data-invitation-id="${inv.id}">
            <div>
                <span class="fw-bold">${escapeHtml(inv.invitee.name)}</span>
                <small class="text-muted d-block">${escapeHtml(inv.invitee.email)}</small>
            </div>
            ${(window.CURRENT_USER === groupData.admin_id || window.CURRENT_USER === inv.inviter.id) ?
            `<button class="btn btn-outline-danger btn-sm cancel-invite-btn" data-id="${inv.id}">
                Cancel
            </button>` : ''}
        </li>
    `).join('');

    // Add click listener for the cancel buttons
    invitesList.querySelectorAll('.cancel-invite-btn').forEach(button => {
        button.addEventListener('click', handleCancelInvitation);
    });
}

// Show/hide admin tools based on user role
function setupUserPermissions() {
    const isAdmin = currentMember && currentMember.user.id === groupData.admin_id;

    if (isAdmin) {
        document.getElementById('adminToolsAccordion').style.display = 'block';
        document.getElementById('memberActionsAccordion').style.display = 'none';
    } else {
        document.getElementById('adminToolsAccordion').style.display = 'none';
        document.getElementById('memberActionsAccordion').style.display = 'block';
    }
}

// Update all dynamic links
function updateLinks() {
    const groupId = window.GROUP_ID;

    // Update all links with group_id
    document.getElementById('recurringExpensesLink').href = `/groups/${groupId}/recurring-expenses`;
    document.getElementById('addExpenseLink').href = `/groups/${groupId}/expenses/0`;
    document.getElementById('addRecurringExpenseLink').href = `/groups/${groupId}/add-recurring-expense`;
    document.getElementById('viewAllExpensesLink').href = `/groups/${groupId}/expenses`;
    // document.getElementById('viewAllExpensesLink2').href = `/groups/${groupId}/expenses`;
    document.getElementById('viewHistoryLink').href = `/groups/${groupId}/view-audit`;
    document.getElementById('deleteGroupLink').href = `/groups/${groupId}/delete-group`;
    document.getElementById('viewPaymentsLink').href = `/groups/${groupId}/payments`;
}

// Initialize page
async function initializePage() {
    console.log('✅ initializePage called');
    showLoading();

    try {
        // Fetch all data in parallel
        await Promise.all([
            fetchGroupDetails(),
            fetchGroupMembers(),
            fetchGroupBalances(),
            fetchPendingInvites()
        ]);

        // Display all data
        displayGroupInfo();
        displayMembers();
        displayBalances();
        displayBalanceDetails();
        displayPendingInvites();
        setupUserPermissions();
        updateLinks();
        setupPaymentModal();

        showContent();
    } catch (error) {
        console.error('Error initializing page:', error);
        showError(error.message || 'Failed to load group details. Please try again.');
    }
}



// --- CODE TO HANDLE ADD MEMBER FORM ---
async function handleAddMember(event) {
    event.preventDefault(); // Stop the form from doing a full-page reload

    const form = event.target;
    const submitButton = form.querySelector('button[type="submit"]');
    const originalButtonText = submitButton.innerHTML;

    // Show a loading state on the button
    submitButton.disabled = true;
    submitButton.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Adding...';

    // Get the email from the input
    const email = document.getElementById('addMemberEmailInput').value;

    try {
        const response = await fetch(`/api/groups/${window.GROUP_ID}/members`, {
            method: 'POST',
            credentials: 'include',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email: email }) // Send the data as JSON
        });

        const result = await response.json();

        if (!response.ok) {
            // Use the error message from  API route
            throw new Error(result.detail || 'Failed to add member');
        }

        alert('Member added successfully!');
        window.location.reload();

    } catch (error) {
        console.error('Error adding member:', error);
        alert(`Error: ${error.message}`);
    } finally {
        // Restore the button text
        submitButton.disabled = false;
        submitButton.innerHTML = originalButtonText;
    }
}

// --- CODE TO HANDLE REMOVE MEMBER FORM ---
async function handleRemoveMember(event) {
    event.preventDefault();

    const form = event.target;
    const submitButton = form.querySelector('button[type="submit"]');
    const originalButtonText = submitButton.innerHTML;

    submitButton.disabled = true;
    submitButton.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Removing...';

    const email = document.getElementById('removeMemberEmailInput').value;

    try {
        const response = await fetch(`/api/groups/${GROUP_ID}/members`, {
            method: 'DELETE',
            credentials: 'include',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email: email })
        });

        if (response.status === 204) {
            alert('Member removed successfully!');
            window.location.reload();
            return;
        }

        const result = await response.json();
        if (!response.ok) {
            throw new Error(result.detail || 'Failed to remove member');
        }

    } catch (error) {
        console.error('Error removing member:', error);
        alert(`Error: ${error.message}`);
    } finally {
        submitButton.disabled = false;
        submitButton.innerHTML = originalButtonText;
    }
}

// CODE TO HANDLE INVITE MEMBER FORM ---
async function handleInviteMember(event) {
    event.preventDefault();
    const form = event.target;
    const submitButton = form.querySelector('button[type="submit"]');
    const originalButtonText = submitButton.innerHTML;

    submitButton.disabled = true;
    submitButton.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Sending...';

    const email = document.getElementById('inviteMemberEmailInput').value;

    try {
        const response = await fetch(`/api/groups/${window.GROUP_ID}/invitations`, {
            method: 'POST',
            credentials: 'include',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ invitee_email: email })
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.detail || 'Failed to send invitation');
        }

        alert('Invitation sent successfully!');

        // Refresh pending invites list
        await fetchPendingInvites();
        displayPendingInvites();

        // Hide the modal
        const modalEl = document.getElementById('inviteMemberModal');
        const modal = bootstrap.Modal.getInstance(modalEl);
        modal.hide();
        form.reset(); // Clear the form

    } catch (error) {
        console.error('Error sending invite:', error);
        alert(`Error: ${error.message}`);
    } finally {
        submitButton.disabled = false;
        submitButton.innerHTML = originalButtonText;
    }
}

// --- NEW: Handle Cancel Invitation ---
async function handleCancelInvitation(event) {
    const button = event.target;
    const invitationId = button.dataset.id;

    if (!confirm('Are you sure you want to cancel this invitation?')) {
        return;
    }

    button.disabled = true;
    button.textContent = 'Canceling...';

    try {
        const response = await fetch(`/api/invitations/${invitationId}`, {
            method: 'DELETE',
            credentials: 'include',
        });

        if (response.status === 204) {
            // Success, no content
            alert('Invitation canceled.');
            // Remove the item from the list
            const listItem = button.closest('li');
            listItem.parentNode.removeChild(listItem);

            // Check if list is now empty
            const list = document.getElementById('pendingInvitesList');
            if (list.children.length === 0) {
                list.innerHTML =
                    '<li class="list-group-item text-muted">No pending invitations.</li>';
                // Update badge
                document.getElementById('pendingInvitesCount').textContent = '0';
            } else {
                // Update badge
                document.getElementById('pendingInvitesCount').textContent = list.children.length;
            }
        } else {
            const result = await response.json();
            throw new Error(result.detail || 'Failed to cancel invitation');
        }

    } catch (error) {
        console.error('Error canceling invitation:', error);
        alert(`Error: ${error.message}`);
        button.disabled = false;
        button.textContent = 'Cancel';
    }
}

// --- CODE TO HANDLE CHANGE ADMIN FORM ---
async function handleChangeAdmin(event) {
    event.preventDefault();

    const form = event.target;
    const submitButton = form.querySelector('button[type="submit"]');
    const originalButtonText = submitButton.innerHTML;

    submitButton.disabled = true;
    submitButton.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Changing...';

    const email = document.getElementById('changeAdminEmailInput').value;

    try {
        const response = await fetch(`/api/groups/${GROUP_ID}/change-admin`, {
            method: 'PATCH',
            credentials: 'include',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ new_admin_email: email })
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.detail || 'Failed to change admin');
        }

        alert('Admin changed successfully!');
        window.location.reload();

    } catch (error) {
        console.error('Error changing admin:', error);
        alert(`Error: ${error.message}`);
    } finally {
        submitButton.disabled = false;
        submitButton.innerHTML = originalButtonText;
    }
}

// --- Handle Edit Group Form ---
async function handleEditGroup(event) {
    event.preventDefault(); // Stop default form submission
    const form = event.target;
    const submitButton = form.querySelector('button[type="submit"]');
    const originalButtonText = submitButton.innerHTML;

    submitButton.disabled = true;
    submitButton.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Saving...';

    // Get the values from the form inputs
    const name = form.querySelector('#groupName').value;
    const description = form.querySelector('#groupDescription').value;

    try {
        const response = await fetch(`/api/groups/${window.GROUP_ID}`, {
            method: 'PATCH', // PATCH as defined in the API
            credentials: 'include',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name: name,
                description: description
            })
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.detail || 'Failed to update group');
        }

        // --- SUCCESS! ---
        alert('Group updated successfully!');
        window.location.reload(); // Reload to show new group name

    } catch (error) {
        console.error('Error updating group:', error);
        alert(`Error: ${error.message}`);
    } finally {
        submitButton.disabled = false;
        submitButton.innerHTML = originalButtonText;
    }
}

async function handleDeleteGroup(event) {
    event.preventDefault();

    // Ask for user confirmation
    const confirmed = confirm("Are you sure you want to delete this group? This action cannot be undone.");
    if (!confirmed) return;

    const deleteButton = event.target;
    const originalText = deleteButton.innerText;

    // Disable button and show spinner text
    deleteButton.classList.add('disabled');
    deleteButton.innerText = 'Deleting...';

    try {
        const response = await fetch(`/api/groups/${window.GROUP_ID}`, {
            method: 'DELETE',
            credentials: 'include'
        });

        if (response.status === 204) {
            alert('Group deleted successfully!');
            window.location.href = '/groups'; // redirect to group list or home
        } else {
            const result = await response.json();
            throw new Error(result.detail || 'Failed to delete group');
        }

    } catch (error) {
        console.error('Error deleting group:', error);
        alert(`Error: ${error.message}`);
    } finally {
        deleteButton.classList.remove('disabled');
        deleteButton.innerText = originalText;
    }
}

//--- Handle View History ---
async function handleViewHistory(event) {
    event.preventDefault();

    try {
        const response = await fetch(`/api/groups/${window.GROUP_ID}/audits`, {
            method: 'GET',
            credentials: 'include'
        });

        if (!response.ok) {
            const result = await response.json();
            throw new Error(result.detail || 'Failed to fetch audit history');
        }

        const audits = await response.json();

        if (audits.length === 0) {
            alert('No audit history found for this group.');
            return;
        }

        // Build a simple string for display
        const historyText = audits
            .map(a => `• ${a.change_description}`)
            .join('\n');

        alert(`Audit History:\n\n${historyText}`);

    } catch (error) {
        console.error('Error fetching audit history:', error);
        alert(`Error: ${error.message}`);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const viewHistoryLink = document.getElementById('viewHistoryLink');
    if (viewHistoryLink) {
        viewHistoryLink.addEventListener('click', handleViewHistory);
    }
});

// ===============================================
// PAYMENT MODAL FUNCTIONALITY
// ===============================================

// Populate member dropdowns for payment modal
function populatePaymentMemberDropdowns() {
    const addPayerSelect = document.getElementById('addPayerId');
    const addPayeeSelect = document.getElementById('addPayeeId');

    console.log(' Attempting to populate payment dropdowns');
    console.log('membersData:', membersData);
    console.log('Payer dropdown element:', addPayerSelect);
    console.log('Payee dropdown element:', addPayeeSelect);

    if (!membersData || membersData.length === 0) {
        console.warn('No members available for payment modal');
        return;
    }

    const options = membersData.map(member =>
        `<option value="${member.user.id}">${member.user.name}</option>`
    ).join('');

    if (addPayerSelect) {
        addPayerSelect.innerHTML = '<option value="">Select payer...</option>' + options;
    }
    if (addPayeeSelect) {
        addPayeeSelect.innerHTML = '<option value="">Select payee...</option>' + options;
    }
}

// Setup payment modal - called AFTER members are loaded
function setupPaymentModal() {
    const addPaymentModal = document.getElementById('addPaymentModal');

    if (addPaymentModal) {
        addPaymentModal.addEventListener('show.bs.modal', () => {
            const today = new Date().toISOString().split('T')[0];
            document.getElementById('addPaymentDate').value = today;
            populatePaymentMemberDropdowns();
        });
    }

    // Handle add payment submission
    const confirmAddPaymentBtn = document.getElementById('confirmAddPaymentBtn');
    if (confirmAddPaymentBtn) {
        confirmAddPaymentBtn.addEventListener('click', async () => {
            const amount = parseFloat(document.getElementById('addAmount').value);
            const paymentDate = document.getElementById('addPaymentDate').value;
            const payerId = parseInt(document.getElementById('addPayerId').value);
            const payeeId = parseInt(document.getElementById('addPayeeId').value);

            if (!amount || amount <= 0) {
                alert('Please enter a valid amount');
                return;
            }
            if (!paymentDate) {
                alert('Please select a payment date');
                return;
            }
            if (!payerId || !payeeId) {
                alert('Please select both payer and payee');
                return;
            }
            if (payerId === payeeId) {
                alert('Payer and payee cannot be the same person');
                return;
            }

            const button = confirmAddPaymentBtn;
            const originalText = button.innerHTML;
            button.disabled = true;
            button.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Recording...';

            try {
                const response = await fetch(
                    `/api/groups/${window.GROUP_ID}/payments`,
                    {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        credentials: 'include',
                        body: JSON.stringify({
                            payer_id: payerId,
                            payee_id: payeeId,
                            amount,
                            payment_date: paymentDate
                        })
                    }
                );

                if (response.ok) {
                    const modal = bootstrap.Modal.getInstance(addPaymentModal);
                    modal.hide();
                    document.getElementById('addPaymentForm').reset();
                    alert('Payment recorded successfully!');
                    // Refresh balances
                    await fetchGroupBalances();
                    displayBalances();
                    displayBalanceDetails();
                } else {
                    const error = await response.json();
                    throw new Error(error.detail || 'Failed to record payment');
                }
            } catch (error) {
                console.error('Error recording payment:', error);
                alert(`Error: ${error.message}`);
            } finally {
                button.disabled = false;
                button.innerHTML = originalText;
            }
        });
    }
}

// This code listens for ANY modal to open on the page
document.addEventListener('show.bs.modal', (event) => {
    const modal = event.target;

    // Find the form inside that specific modal
    const form = modal.querySelector('form');
    if (!form) return;


    if (form.id === 'addMemberModalForm') {
        // add .once to avoid attaching the same listener 20 times
        form.addEventListener('submit', handleAddMember, { once: true });
    }
    else if (form.id === 'removeMemberModalForm') {
        form.addEventListener('submit', handleRemoveMember, { once: true });
    }
    else if (form.id === 'changeAdminModalForm') {
        form.addEventListener('submit', handleChangeAdmin, { once: true });
    }
    else if (form.id === 'editGroupModalForm') {
        form.addEventListener('submit', handleEditGroup, { once: true });
    }
    else if (form.id === 'inviteMemberModalForm') {
        form.addEventListener('submit', handleInviteMember, { once: true });
    }
});

document.addEventListener('DOMContentLoaded', () => {
    const deleteGroupLink = document.getElementById('deleteGroupLink');
    if (deleteGroupLink) {
        deleteGroupLink.addEventListener('click', handleDeleteGroup);
    }
});



// 1. Initialize the main page content on load
document.addEventListener('DOMContentLoaded', initializePage);


document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('invitationsContainer');
    
    // Fetch and display invitations on page load
    fetchMyInvitations();

    async function fetchMyInvitations() {
        showLoading();
        try {
            const response = await fetch('/api/invitations/me', {
                credentials: 'include'
            });

            if (!response.ok) {
                throw new Error('Failed to load invitations.');
            }
            
            const invitations = await response.json();
            displayInvitations(invitations);

        } catch (error) {
            displayError(error.message);
        }
    }

    function showLoading() {
        container.innerHTML = `
            <div class="text-center">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mt-2 text-muted">Loading your invitations...</p>
            </div>`;
    }

    function displayError(message) {
        container.innerHTML = `<div class="alert alert-danger">${message}</div>`;
    }

    function displayInvitations(invitations) {
        if (invitations.length === 0) {
            container.innerHTML = `
                <div class="alert alert-info">
                    You have no pending invitations.
                </div>`;
            return;
        }

        container.innerHTML = invitations.map(inv => `
            <div class="card mb-3" data-invitation-id="${inv.id}">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <h5 class="card-title mb-1">
                                You're invited to join <strong>${escapeHtml(inv.group.name)}</strong>
                            </h5>
                            <small class="text-muted">
                                Invited by ${escapeHtml(inv.inviter.name)} (${escapeHtml(inv.inviter.email)})
                            </small>
                        </div>
                        <div class="invitation-actions flex-shrink-0 ms-3">
                            <button class="btn btn-success btn-sm respond-btn" data-action="accept" data-id="${inv.id}">
                                Accept
                            </button>
                            <button class="btn btn-danger btn-sm respond-btn" data-action="decline" data-id="${inv.id}">
                                Decline
                            </button>
                        </div>
                        <div class="invitation-result d-none text-muted">
                            </div>
                    </div>
                </div>
            </div>
        `).join('');
        
        // Add event listeners to all new buttons
        container.querySelectorAll('.respond-btn').forEach(button => {
            button.addEventListener('click', handleInvitationResponse);
        });
    }

    async function handleInvitationResponse(event) {
        const button = event.target;
        const action = button.dataset.action;
        const invitationId = button.dataset.id;
        
        // Find the parent card and action/result elements
        const card = button.closest('.card');
        const actionDiv = card.querySelector('.invitation-actions');
        const resultDiv = card.querySelector('.invitation-result');

        // Disable buttons
        actionDiv.querySelectorAll('button').forEach(btn => btn.disabled = true);

        try {
            const response = await fetch(`/api/invitations/${invitationId}`, {
                method: 'PATCH',
                credentials: 'include',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: action })
            });

            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.detail || 'Response failed');
            }

            // Success
            actionDiv.classList.add('d-none');
            resultDiv.classList.remove('d-none');
            if (action === 'accept') {
                resultDiv.innerHTML = '<strong>Accepted!</strong> You are now a member.';
                resultDiv.classList.add('text-success');
            } else {
                resultDiv.innerHTML = '<strong>Declined.</strong> The invitation has been removed.';
            }

        } catch (error) {
            // Re-enable buttons on failure
            actionDiv.querySelectorAll('button').forEach(btn => btn.disabled = false);
            resultDiv.classList.remove('d-none');
            resultDiv.classList.add('text-danger');
            resultDiv.textContent = `Error: ${error.message}`;
        }
    }

    function escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
});
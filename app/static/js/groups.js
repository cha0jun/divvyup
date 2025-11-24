// Store all groups data globally
let allGroupsData = [];
const INITIAL_DISPLAY_COUNT = 3;
let currentDisplayCount = INITIAL_DISPLAY_COUNT;

document.addEventListener('DOMContentLoaded', () => {
    fetchGroups();
});

async function fetchGroups() {
    const container = document.getElementById('groupsContainer');
    const loadingState = document.getElementById('loadingState');

    try {
        const response = await fetch('/api/groups');

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const groups = await response.json();
        allGroupsData = groups;

        // Hide loading state
        loadingState.style.display = 'none';

        // Display groups
        displayGroups(groups);

    } catch (error) {
        displayError(error);
    }
}

function displayGroups(groups) {
    const container = document.getElementById('groupsContainer');
    const loadMoreContainer = document.getElementById('loadMoreContainer');

    if (groups.length === 0) {
        displayEmptyState();
        return;
    }

    // Clear container
    container.innerHTML = '';

    // Display groups up to currentDisplayCount
    const groupsToShow = groups.slice(0, currentDisplayCount);

    groupsToShow.forEach(group => {
        const groupCard = createGroupCard(group);
        container.appendChild(groupCard);
    });

    // Show/hide Load More button
    if (groups.length > currentDisplayCount) {
        loadMoreContainer.style.display = 'block';
    } else {
        loadMoreContainer.style.display = 'none';
    }
}

function createGroupCard(group) {
    // Create column div
    const colDiv = document.createElement('div');
    colDiv.className = 'col-md-4';

    // Format date
    const createdDate = new Date(group.created_on).toLocaleDateString();

    // Build card HTML
    colDiv.innerHTML = `
    <div class="card h-100 shadow-sm">
        <div class="card-body">
            <h5 class="card-title">${escapeHtml(group.name)}</h5>
            <p class="card-text text-muted">${escapeHtml(group.description || 'No description')}</p>
            <div class="mb-3">
                <a href="/groups/${group.id}/expenses" class="text-decoration-none">
                    <span class="badge bg-info">Expenses</span>
                </a>
            </div>
            <p class="text-muted small mb-0">
                <i class="bi bi-calendar"></i> Created: ${createdDate}
            </p>
            <p class="text-muted small">
                <i class="bi bi-person"></i> Admin ID: ${group.admin_id}
            </p>
        </div>
        <div class="card-footer bg-white border-top">
            <a href="/groups/${group.id}" class="btn btn-primary btn-sm">View Group</a>
        </div>
    </div>
    `;

    return colDiv;
}

function displayEmptyState() {
    const container = document.getElementById('groupsContainer');
    container.innerHTML = `
    <div class="col-12">
        <div class="alert alert-info text-center" role="alert">
            <h4 class="alert-heading">No groups yet!</h4>
            <p>You haven't joined or created any expense groups.</p>
            <hr>
                <a href="#" class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#createGroupModal">
                    Create Your First Group
                </a>
        </div>
    </div>
    `;
}

function displayError(error) {
    console.error('Error fetching groups:', error);
    const container = document.getElementById('groupsContainer');
    const loadingState = document.getElementById('loadingState');

    loadingState.style.display = 'none';

    container.innerHTML = `
    <div class="col-12">
        <div class="alert alert-danger text-center" role="alert">
            <h4 class="alert-heading">Error Loading Groups</h4>
            <p>Failed to load your groups. Please try again.</p>
            <button class="btn btn-danger" onclick="location.reload()">Retry</button>
        </div>
    </div>
    `;
}

function loadMoreGroups() {
    currentDisplayCount += INITIAL_DISPLAY_COUNT;
    displayGroups(allGroupsData);
}

// Add event listener to Load More button
document.getElementById('loadMoreBtn').addEventListener('click', loadMoreGroups);

// Helper function to escape HTML (prevent XSS)
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// For Create New Group Modal
document.addEventListener("DOMContentLoaded", () => {
    const form = document.querySelector('form[action="/groups/create"]');

    form.addEventListener("submit", async (e) => {
        e.preventDefault(); // prevent normal form submission

        const data = {
            name: document.getElementById("groupName").value,
            description: document.getElementById("groupDescription").value
        };

        const response = await fetch("/api/groups", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data)
        });

        if (response.ok) {
            // Close the modal
            const modalEl = document.getElementById("createGroupModal");
            const modal = bootstrap.Modal.getInstance(modalEl);
            modal.hide();

            // Optionally reload group list
            location.reload();
        } else {
            console.error("Failed to create group");
        }
    });
});

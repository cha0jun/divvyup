let payments = [];
let members = [];
let groupData = null;
let currentPaymentId = null;

document.addEventListener('DOMContentLoaded', () => {
    const deleteModal = new bootstrap.Modal(document.getElementById('deletePaymentModal'));
    const editModal = new bootstrap.Modal(document.getElementById('editPaymentModal'));

    fetchGroupData();
    fetchMembers();
    fetchPayments();

    async function fetchGroupData() {
        try {
            const response = await fetch(`/api/groups/${window.GROUP_ID}`, { credentials: 'include' });
            if (!response.ok) throw new Error('Failed to fetch group data');

            groupData = await response.json();
        } catch (error) {
            console.error('Error fetching group data:', error);
        }
    }

    // Populate member dropdowns
    function populateMemberDropdowns() {
        const editPayerSelect = document.getElementById('editPayerId');
        const editPayeeSelect = document.getElementById('editPayeeId');

        if (members.length === 0) {
            console.warn('No members available yet');
            return;
        }

        const options = members.map(member =>
            `<option value="${member.user.id}">${member.user.name}</option>`
        ).join('');

        // Populate edit modal dropdowns
        if (editPayerSelect) {
            editPayerSelect.innerHTML = '<option value="">Select payer...</option>' + options;
        }
        if (editPayeeSelect) {
            editPayeeSelect.innerHTML = '<option value="">Select payee...</option>' + options;
        }

    }

    // Check if user can edit/delete a payment
    function canModifyPayment(payment) {
        const isAdmin = groupData && window.CURRENT_USER === groupData.admin_id;
        const isCreator = payment.created_by === window.CURRENT_USER;

        return isAdmin || isCreator;
    }


    // Render payments table
    function renderPayments() {
        const tbody = document.getElementById('paymentsTableBody');
        const emptyState = document.getElementById('emptyState');
        const tableContainer = document.getElementById('paymentsTableContainer');

        if (payments.length === 0) {
            emptyState.style.display = 'block';
            tableContainer.style.display = 'none';
            return;
        }

        emptyState.style.display = 'none';
        tableContainer.style.display = 'block';

        tbody.innerHTML = payments.map(payment => {
            const paymentDate = new Date(payment.payment_date).toLocaleDateString();
            const amount = parseFloat(payment.amount).toFixed(2);
            const canModify = canModifyPayment(payment);

            // Only show buttons if user has permission
            const actionButtons = canModify ? `
                <button class="btn btn-sm btn-outline-primary me-2" onclick="handleEdit(${payment.id})">
                    Edit
                </button>
                <button class="btn btn-sm btn-outline-danger" onclick="handleDelete(${payment.id})">
                    Delete
                </button>
            ` : '<span class="text-muted small">No actions available</span>';


            return `
        <tr data-payment-id="${payment.id}">
            <td>${paymentDate}</td>
            <td>${payment.payer.name}</td>
            <td>${payment.payee.name}</td>
            <td>$${amount}</td>
            <td>${actionButtons}</td>
        </tr>
        `;
        }).join('');
    }


    // Handle edit
    window.handleEdit = function (paymentId) {
        const payment = payments.find(p => p.id === paymentId);
        if (!payment) return;

        // Double-check permission before opening modal
        if (!canModifyPayment(payment)) {
            alert('You do not have permission to edit this payment.');
            return;
        }

        currentPaymentId = paymentId;

        document.getElementById('editAmount').value = payment.amount;
        document.getElementById('editPaymentDate').value = payment.payment_date.split('T')[0];
        document.getElementById('editPayerId').value = payment.payer_id;
        document.getElementById('editPayeeId').value = payment.payee_id;

        editModal.show();
    };

    window.handleDelete = function (paymentId) {
        const payment = payments.find(p => p.id === paymentId);
        if (!payment) return;

        // Double-check permission before opening modal
        if (!canModifyPayment(payment)) {
            alert('You do not have permission to delete this payment.');
            return;
        }

        currentPaymentId = paymentId;
        deleteModal.show();
    };

    // Confirm delete
    document.getElementById('confirmDeleteBtn').addEventListener('click', async () => {
        if (!currentPaymentId) return;

        try {
            const response = await fetch(
                `/api/groups/${window.GROUP_ID}/payments/${currentPaymentId}`,
                { method: 'DELETE', credentials: 'include' }
            );

            if (response.ok) {
                deleteModal.hide();
                await fetchPayments();
                alert('Payment deleted successfully!');
            } else {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to delete payment');
            }
        } catch (error) {
            console.error('Error deleting payment:', error);
            alert(`Error: ${error.message}`);
        }
    });

    // Confirm edit
    document.getElementById('confirmEditBtn').addEventListener('click', async () => {
        if (!currentPaymentId) return;

        const amount = parseFloat(document.getElementById('editAmount').value);
        const paymentDate = document.getElementById('editPaymentDate').value;
        const payerId = parseInt(document.getElementById('editPayerId').value);
        const payeeId = parseInt(document.getElementById('editPayeeId').value);

        if (!amount || amount <= 0) { alert('Please enter a valid amount'); return; }
        if (!paymentDate) { alert('Please select a payment date'); return; }
        if (!payerId || !payeeId) { alert('Please select both payer and payee'); return; }
        if (payerId === payeeId) { alert('Payer and payee cannot be the same person'); return; }

        try {
            const response = await fetch(
                `/api/groups/${window.GROUP_ID}/payments/${currentPaymentId}`,
                {
                    method: 'PATCH',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'include',
                    body: JSON.stringify({ payer_id: payerId, payee_id: payeeId, amount, payment_date: paymentDate })
                }
            );

            if (response.ok) {
                editModal.hide();
                await fetchPayments();
                alert('Payment updated successfully!');
            } else {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to update payment');
            }
        } catch (error) {
            console.error('Error updating payment:', error);
            alert(`Error: ${error.message}`);
        }
    });

    // Fetch members
    async function fetchMembers() {
        try {
            const response = await fetch(`/api/groups/${window.GROUP_ID}/members`, { credentials: 'include' });
            if (!response.ok) throw new Error('Failed to fetch group members');

            const membersData = await response.json();
            members = membersData || [];
            populateMemberDropdowns();
        } catch (error) {
            console.error('Error fetching members:', error);
        }
    }

    // Fetch payments
    async function fetchPayments() {
        try {
            const response = await fetch(`/api/groups/${window.GROUP_ID}/payments`, { credentials: 'include' });
            if (!response.ok) throw new Error('Failed to fetch payments');

            payments = await response.json();
            renderPayments();
        } catch (error) {
            console.error('Error fetching payments:', error);
            alert(`Error: ${error.message}`);
        } finally {
            document.getElementById('loadingSpinner').style.display = 'none';
        }
    }
});


// let payments = [];
// let members = [];
// let currentPaymentId = null;
// const deleteModal = new bootstrap.Modal(document.getElementById('deletePaymentModal'));
// const editModal = new bootstrap.Modal(document.getElementById('editPaymentModal'));

// // Fetch payments on page load
// async function fetchPayments() {
//     try {
//         const response = await fetch(`/api/groups/${window.GROUP_ID}/payments`, {
//             credentials: 'include'
//         });

//         if (!response.ok) {
//             throw new Error('Failed to fetch payments');
//         }

//         payments = await response.json();
//         renderPayments();

//     } catch (error) {
//         console.error('Error fetching payments:', error);
//         alert(`Error: ${error.message}`);
//     } finally {
//         document.getElementById('loadingSpinner').style.display = 'none';
//     }
// }

// // Fetch group members for dropdowns
// async function fetchMembers() {
//     try {
//         const response = await fetch(`/api/groups/${window.GROUP_ID}/members`, {
//             credentials: 'include'
//         });

//         if (!response.ok) {
//             throw new Error('Failed to fetch group members');
//         }

//         const membersData = await response.json();
//         members = membersData || [];
//         populateMemberDropdowns();

//     } catch (error) {
//         console.error('Error fetching members:', error);
//     }
// }

// // Populate payer and payee dropdowns
// function populateMemberDropdowns() {
//     const payerSelect = document.getElementById('editPayerId');
//     const payeeSelect = document.getElementById('editPayeeId');

//     const options = members.map(member =>
//         `<option value="${member.user.id}">${member.user.name}</option>`
//     ).join('');

//     payerSelect.innerHTML = '<option value="">Select payer...</option>' + options;
//     payeeSelect.innerHTML = '<option value="">Select payee...</option>' + options;
// }

// // Render payments table
// function renderPayments() {
//     const tbody = document.getElementById('paymentsTableBody');
//     const emptyState = document.getElementById('emptyState');
//     const tableContainer = document.getElementById('paymentsTableContainer');

//     if (payments.length === 0) {
//         emptyState.style.display = 'block';
//         tableContainer.style.display = 'none';
//         return;
//     }

//     emptyState.style.display = 'none';
//     tableContainer.style.display = 'block';

//     tbody.innerHTML = payments.map(payment => {
//         const paymentDate = new Date(payment.payment_date).toLocaleDateString();
//         const amount = parseFloat(payment.amount).toFixed(2);

//         return `
//     <tr data-payment-id="${payment.id}">
//         <td>${paymentDate}</td>
//         <td>${payment.payer.name}</td>
//         <td>${payment.payee.name}</td>
//         <td>$${amount}</td>
//         <td>
//             <button class="btn btn-sm btn-outline-primary me-2" onclick="handleEdit(${payment.id})">
//                 Edit
//             </button>
//             <button class="btn btn-sm btn-outline-danger" onclick="handleDelete(${payment.id})">
//                 Delete
//             </button>
//         </td>
//     </tr>
//     `;
//     }).join('');
// }

// // Handle edit button click
// function handleEdit(paymentId) {
//     const payment = payments.find(p => p.id === paymentId);
//     if (!payment) return;

//     currentPaymentId = paymentId;

//     // Populate form with current values
//     document.getElementById('editAmount').value = payment.amount;
//     document.getElementById('editPaymentDate').value = payment.payment_date.split('T')[0];
//     document.getElementById('editPayerId').value = payment.payer_id;
//     document.getElementById('editPayeeId').value = payment.payee_id;

//     editModal.show();
// }

// // Handle delete button click
// function handleDelete(paymentId) {
//     currentPaymentId = paymentId;
//     deleteModal.show();
// }

// // Confirm delete
// document.getElementById('confirmDeleteBtn').addEventListener('click', async () => {
//     if (!currentPaymentId) return;

//     try {
//         const response = await fetch(
//             `/api/groups/${window.GROUP_ID}/payments/${currentPaymentId}`,
//             {
//                 method: 'DELETE',
//                 credentials: 'include'
//             }
//         );

//         if (response.ok) {
//             deleteModal.hide();
//             await fetchPayments(); // Refresh the list
//             alert('Payment deleted successfully!');
//         } else {
//             const error = await response.json();
//             throw new Error(error.detail || 'Failed to delete payment');
//         }

//     } catch (error) {
//         console.error('Error deleting payment:', error);
//         alert(`Error: ${error.message}`);
//     }
// });

// // Code for updating payment
// document.getElementById('confirmEditBtn').addEventListener('click', async () => {
//     if (!currentPaymentId) return;

//     const amount = parseFloat(document.getElementById('editAmount').value);
//     const paymentDate = document.getElementById('editPaymentDate').value;
//     const payerId = parseInt(document.getElementById('editPayerId').value);
//     const payeeId = parseInt(document.getElementById('editPayeeId').value);

//     // Validation
//     if (!amount || amount <= 0) {
//         alert('Please enter a valid amount');
//         return;
//     }

//     if (!paymentDate) {
//         alert('Please select a payment date');
//         return;
//     }

//     if (!payerId || !payeeId) {
//         alert('Please select both payer and payee');
//         return;
//     }

//     if (payerId === payeeId) {
//         alert('Payer and payee cannot be the same person');
//         return;
//     }

//     try {
//         const response = await fetch(`/api/groups/${window.GROUP_ID}/payments/${currentPaymentId}`, {
//             method: 'PATCH',
//             headers: { 'Content-Type': 'application/json' },
//             credentials: 'include',
//             body: JSON.stringify({
//                 payer_id: payerId,
//                 payee_id: payeeId,
//                 amount: amount,
//                 payment_date: paymentDate
//             })
//         });

//         if (response.ok) {
//             editModal.hide();
//             await fetchPayments(); // Refresh the list
//             alert('Payment updated successfully!');
//         } else {
//             const error = await response.json();
//             throw new Error(error.detail || 'Failed to update payment');
//         }

//     } catch (error) {
//         console.error('Error updating payment:', error);
//         alert(`Error: ${error.message}`);
//     }
// });

// // Initialize
// fetchMembers();
// fetchPayments();

let payments = [];
let members = [];
let currentPaymentId = null;

document.addEventListener('DOMContentLoaded', () => {
    // Initialize modals
    const deleteModal = new bootstrap.Modal(document.getElementById('deletePaymentModal'));
    const editModal = new bootstrap.Modal(document.getElementById('editPaymentModal'));

    // Fetch data after DOM is ready
    fetchMembers();
    fetchPayments();

    // Populate member dropdowns
    function populateMemberDropdowns() {
        const payerSelect = document.getElementById('editPayerId');
        const payeeSelect = document.getElementById('editPayeeId');

        const options = members.map(member =>
            `<option value="${member.user.id}">${member.user.name}</option>`
        ).join('');

        payerSelect.innerHTML = '<option value="">Select payer...</option>' + options;
        payeeSelect.innerHTML = '<option value="">Select payee...</option>' + options;
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

            return `
        <tr data-payment-id="${payment.id}">
            <td>${paymentDate}</td>
            <td>${payment.payer.name}</td>
            <td>${payment.payee.name}</td>
            <td>$${amount}</td>
            <td>
                <button class="btn btn-sm btn-outline-primary me-2" onclick="handleEdit(${payment.id})">
                    Edit
                </button>
                <button class="btn btn-sm btn-outline-danger" onclick="handleDelete(${payment.id})">
                    Delete
                </button>
            </td>
        </tr>
        `;
        }).join('');
    }

    // Handle edit
    window.handleEdit = function (paymentId) {
        const payment = payments.find(p => p.id === paymentId);
        if (!payment) return;

        currentPaymentId = paymentId;

        document.getElementById('editAmount').value = payment.amount;
        document.getElementById('editPaymentDate').value = payment.payment_date.split('T')[0];
        document.getElementById('editPayerId').value = payment.payer_id;
        document.getElementById('editPayeeId').value = payment.payee_id;

        editModal.show();
    };

    // Handle delete
    window.handleDelete = function (paymentId) {
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

# Testing checklist

## Authentication
- Login with each demo role.
- Try an incorrect password.
- Logout and try opening `/dashboard`.

## Customer
- Create a ticket with a screenshot.
- View the ticket.
- Reply and verify the reply is visible to support users.
- Verify internal notes are not shown to the customer.
- Reopen a resolved ticket.

## Admin
- View/filter/search tickets.
- Add/edit customer, technician and category.
- Assign/reassign a technician.
- Change priority/status.
- Check dashboard cards/charts.
- Check notifications.
- Run reports with filters.

## Technician
- View assigned tickets.
- Add public comment and internal note.
- Upload attachment.
- Move ticket through In Progress, Waiting for Customer and Resolved.

## Security/validation
- Upload an unsupported extension.
- Upload a file over 10 MB.
- Attempt to access another customer's ticket as a customer.
- Attempt an admin-only endpoint as technician/customer.

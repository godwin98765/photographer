// simple mobile menu toggle
const menuToggle = document.querySelector('.menu-toggle');
const navUl = document.querySelector('nav ul');

if(menuToggle){
  menuToggle.addEventListener('click', () => {
    navUl.classList.toggle('show');
  });
}

// Example AJAX call for update/delete photographer from admin page
function updatePhotographer(id) {
  const form = document.getElementById('update-form-' + id);
  const formData = new FormData(form);

  fetch(`/update_photographer/${id}`, {
    method: 'POST',
    body: formData
  })
    .then(res => res.json())
    .then(data => {
      if (data.status === 'success') {
        alert('Updated successfully');
        location.reload();
      }
    });
}

function deletePhotographer(id) {
  if (!confirm('Are you sure you want to delete this photographer?')) return;
  fetch(`/delete_photographer/${id}`, { method: 'POST' })
    .then(res => res.json())
    .then(data => {
      if (data.status === 'deleted') {
        alert('Deleted successfully');
        location.reload();
      }
    });
}

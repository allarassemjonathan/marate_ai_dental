document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('addForm');
  const resultsTable = document.getElementById('resultsTable');
  const searchBox = document.getElementById('searchBox');
  const editModalOverlay = document.getElementById('editModalOverlay');
  const editForm = document.getElementById('editForm');
  
  let currentPatientId = null;

  // Make these functions globally accessible
  window.openInvoiceModal = function(patientId) {
    currentPatientId = patientId;
    document.getElementById('invoiceModal').style.display = 'flex';
    
    // Clear existing items and add one default item
    document.getElementById('invoice-items-container').innerHTML = '';
    addInvoiceItem();
  };

  window.closeInvoiceModal = function() {
    document.getElementById('invoiceModal').style.display = 'none';
    currentPatientId = null;
    document.getElementById('invoice-items-container').innerHTML = '';
  };

  window.addInvoiceItem = function() {
    const itemsContainer = document.getElementById('invoice-items-container');
    const itemDiv = document.createElement('div');
    itemDiv.className = 'grid grid-cols-1 md:grid-cols-4 gap-5 mb-6 p-6 border border-gray-700 rounded-xl';
    
    itemDiv.innerHTML = `
        <div class="relative md:col-span-2">
            <input type="text" placeholder="Nom de l'article" class="item-name input-field w-full p-4 rounded-xl" required>
            <div class="absolute left-0 bottom-0 h-0.5 w-0 bg-gradient-to-r from-cyan-400 to-cyan-400 transition-all duration-300 input-underline"></div>
        </div>
        
        <div class="relative">
            <input type="number" placeholder="Quantité" class="item-quantity input-field w-full p-4 rounded-xl" step="0.01" min="0" required>
            <div class="absolute left-0 bottom-0 h-0.5 w-0 bg-gradient-to-r from-cyan-400 to-cyan-400 transition-all duration-300 input-underline"></div>
        </div>
        
        <div class="relative">
            <input type="number" placeholder="Prix unitaire" class="item-price input-field w-full p-4 rounded-xl" step="0.01" min="0" required>
            <div class="absolute left-0 bottom-0 h-0.5 w-0 bg-gradient-to-r from-cyan-400 to-cyan-400 transition-all duration-300 input-underline"></div>
        </div>
        
        <div class="md:col-span-4 flex justify-end">
            <button type="button" onclick="removeInvoiceItem(this)" class="text-red-400 hover:text-red-300 transition-colors text-sm">
                Supprimer cet article
            </button>
        </div>
    `;
    
    itemsContainer.appendChild(itemDiv);
    
    // Add focus/blur effects to the new inputs
    const newInputs = itemDiv.querySelectorAll('.input-field');
    newInputs.forEach(input => {
        input.addEventListener('focus', function() {
            const underline = this.nextElementSibling;
            if (underline && underline.classList.contains('input-underline')) {
                underline.style.width = '100%';
            }
        });
        
        input.addEventListener('blur', function() {
            const underline = this.nextElementSibling;
            if (underline && underline.classList.contains('input-underline')) {
                underline.style.width = '0';
            }
        });
    });
  };

  window.removeInvoiceItem = function(button) {
    const itemsContainer = document.getElementById('invoice-items-container');
    if (itemsContainer.children.length > 1) {
        button.closest('.grid').remove();
    } else {
        alert('Au moins un article est requis');
    }
  };

  window.generateInvoice = function() {
    if (!currentPatientId) {
        alert('Erreur: Aucun patient sélectionné');
        return;
    }
    
    // Collect all invoice items
    const items = [];
    const itemContainers = document.querySelectorAll('#invoice-items-container .grid');
    
    itemContainers.forEach(container => {
        const name = container.querySelector('.item-name').value.trim();
        const quantity = container.querySelector('.item-quantity').value;
        const price = container.querySelector('.item-price').value;
        
        if (name && quantity && price) {
            items.push({
                name: name,
                quantity: parseFloat(quantity),
                price: parseFloat(price)
            });
        }
    });
    
    if (items.length === 0) {
        alert('Veuillez ajouter au moins un article avec tous les champs remplis');
        return;
    }
    
    // Send to server to generate PDF
    fetch(`/generate_invoice/${currentPatientId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ items: items })
    })
    .then(response => {
        if (response.ok) {
            return response.blob();
        } else {
            throw new Error('Erreur lors de la génération du PDF');
        }
    })
    .then(blob => {
        // Create download link
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = `facture_${currentPatientId}_${new Date().toISOString().slice(0,10)}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        // Close modal
        closeInvoiceModal();
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Erreur lors de la génération du PDF: ' + error.message);
    });
  };

function loadPatients(q = '') {
  fetch(`/search?q=${encodeURIComponent(q)}`)
    .then(res => res.json())
    .then(data => {
      console.log(data);
      resultsTable.innerHTML = '';
      data.forEach(p => {
        const tr = document.createElement('tr');
        tr.className = "cursor-pointer hover:bg-gray-800 transition-colors";
        
        // Open invoice modal when clicking the row
        tr.onclick = () => openInvoiceModal(p.id);

        // Include the created_at field first
        const createdAtTd = document.createElement('td');
        createdAtTd.className = "p-2 border";
        createdAtTd.textContent = p.created_at || '';
        createdAtTd.title = p.created_at || '';
        tr.appendChild(createdAtTd);

        // The rest of the fields
        [
          'name', 'date_of_birth', 'adresse', 'age', 'antecedents_tabagiques', 
          'statut_implants', 'frequence_fil_dentaire', 'frequence_brossage', 'allergies'
        ].forEach(k => {
          const td = document.createElement('td');
          td.className = "p-2 border";
          let content = p[k] || '';
          if (content.length > 30) {
            content = content.substring(0, 30) + '...';
          }
          td.textContent = content;
          td.title = p[k] || '';
          tr.appendChild(td);
        });

        // Action buttons
        const actionTd = document.createElement('td');
        actionTd.className = "p-2 border";
        actionTd.innerHTML = `
          <div class="flex space-x-2 justify-center">
            <button class="text-blue-500 hover:text-blue-700" onclick="event.stopPropagation(); editPatient(${p.id})">Modifier</button>
            <button class="text-red-500 hover:text-red-700" onclick="event.stopPropagation(); deletePatient(${p.id})">Supprimer</button>
            <button class="text-green-500 hover:text-green-700" onclick="event.stopPropagation(); window.location.href='/patient/${p.id}'">Détails</button>
          </div>
        `;
        tr.appendChild(actionTd);

        resultsTable.appendChild(tr);
      });
    });
}
  
  window.deletePatient = function (id) {
    if (confirm('Êtes-vous sûr de vouloir supprimer ce patient?')) {
      fetch(`/delete/${id}`, { method: 'DELETE' })
        .then(res => res.json())
        .then(() => {
          loadPatients(searchBox.value);
        });
    }
  }

  window.editPatient = function(id) {
    fetch(`/get_patient/${id}`)
      .then(res => res.json())
      .then(patient => {
        // Populate the edit form
        document.getElementById('editId').value = patient.id;
        
        // Updated fields array to match new schema
        const fields = ['name', 'date_of_birth', 'adresse', 'age', 
                        'antecedents_tabagiques', 'statut_implants', 'frequence_fil_dentaire', 
                        'frequence_brossage', 'allergies'];
        
        fields.forEach(field => {
          const input = document.getElementById(`edit_${field}`);
          if (input) {
            input.value = patient[field] || '';
          }
        });
        
        // Show the modal
        document.getElementById('editModalOverlay').classList.remove('hidden');
      });
  };

  window.closeEditModal = function() {
    document.getElementById('editModalOverlay').classList.add('hidden');
  };
  
  // Event delegation for clicks outside the modal content
  editModalOverlay.addEventListener('click', (e) => {
    if (e.target === editModalOverlay) {
      closeEditModal();
    }
  });

  // Submit event for the edit form
  editForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const patientId = document.getElementById('editId').value;
    const formData = new FormData(editForm);
    const data = Object.fromEntries(formData.entries());
    
    // Remove the ID field from the data to be sent
    delete data.id;
    
    fetch(`/update/${patientId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    })
    .then(res => res.json())
    .then(result => {
      if (result.status === 'success') {
        closeEditModal();
        loadPatients(searchBox.value);
      } else {
        alert(result.message || 'Error updating patient');
      }
    });
  });

  // Add new patient form submission
  form.addEventListener('submit', e => {
    e.preventDefault();
    const data = Object.fromEntries(new FormData(form).entries());
    fetch('/add', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    })
    .then(res => res.json())
    .then(() => {
      form.reset();
      loadPatients(searchBox.value);
    });
  });

  // Search functionality
  searchBox.addEventListener('input', e => {
    clearTimeout(window.searchTimer);
    window.searchTimer = setTimeout(() => loadPatients(e.target.value), 300);
  });

  // Initial load
  loadPatients();
});
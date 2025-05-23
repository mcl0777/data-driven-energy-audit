document.addEventListener('DOMContentLoaded', function () {
  var uploadForm = document.getElementById('upload-form');
  var currentState = 'standby';
  var dataStore = {
      'standby': {},
      'ready': {},
      'process': {}
  };
  var columnsData = {
      'standby': [],
      'ready': [],
      'process': []
  };
  var totalEnergyColumn = {
      'standby': '',
      'ready': '',
      'process': ''
  };
  var allData = {
      'standby': {},
      'ready': {},
      'process': {}
  };
  var chartTitle = document.getElementById('energy-chart-title');
  var pieChartTitle = document.getElementById('pie-chart-title');
  var pieCanvas = document.getElementById('energyPieChart');
  var tabs = document.getElementById('tabs');

  console.log("Document loaded and scripts initialized.");  // Debugging

  // Tab wechseln
  document.querySelectorAll('.tab-button').forEach(button => {
      button.addEventListener('click', function () {
          var state = this.getAttribute('data-state');
          console.log(`Tab button clicked: ${state}`); // Debugging
          changeState(state);
      });
  });

  // Funktionen für den Zustand wechseln
  function changeState(state) {
      console.log(`Changing state to: ${state}`); // Debugging
      currentState = state;
      document.querySelectorAll('.tab-button').forEach(button => {
          button.classList.remove('active');
      });
      document.querySelector(`.tab-button[data-state="${state}"]`).classList.add('active');
      console.log(`Current dataStore: ${JSON.stringify(dataStore[state])}`); // Debugging
      if (dataStore[state].columns) {
          buildStructureTree(dataStore[state].columns, dataStore[state].totalEnergyColumn, state);
          updateCharts(dataStore[state].component, dataStore[state].columns, dataStore[state].totalEnergyColumn, state);
      } else {
          clearCharts();
      }
  }

  function clearCharts() {
      console.log('Clearing charts'); // Debugging
      chartTitle.style.display = 'none';
      pieChartTitle.style.display = 'none';
      if (Chart.getChart('energyChart')) {
          Chart.getChart('energyChart').destroy();
      }
      if (Chart.getChart('energyPieChart')) {
          Chart.getChart('energyPieChart').destroy();
      }
  }

  // Upload-Formular
  uploadForm.addEventListener('submit', function (e) {
      e.preventDefault(); // Verhindert das automatische Senden des Formulars

      var formData = new FormData();
      formData.append('file-standby', document.getElementById('file-upload-standby').files[0]);
      formData.append('file-ready', document.getElementById('file-upload-ready').files[0]);
      formData.append('file-process', document.getElementById('file-upload-process').files[0]);

      console.log("Form submitted for upload.");  // Debugging

      fetch('/upload', {
          method: 'POST',
          body: formData
      })
      .then(response => response.json())
      .then(data => {
          if (data.error) {
              alert('Error: ' + data.error); // Zeigt eine Fehlermeldung an
              console.error('Upload Error:', data.error); // Protokolliert den Fehler in der Konsole
          } else {
              Object.keys(data).forEach(state => {
                  columnsData[state] = data[state].columns;
                  allData[state] = data[state].data; // Speichert die gesamten Daten
                  console.log(`Uploaded Data for ${state}:`, allData[state]); // Debugging: Daten in der Konsole anzeigen

                  totalEnergyColumn[state] = columnsData[state].reduce((a, b) => {
                      const sumA = allData[state][a].reduce((acc, val) => acc + val, 0);
                      const sumB = allData[state][b].reduce((acc, val) => acc + val, 0);
                      return sumA > sumB ? a : b;
                  });
                  console.log(`Determined total energy column for ${state}: ${totalEnergyColumn[state]}`);

                  dataStore[state] = {
                      columns: columnsData[state],
                      totalEnergyColumn: totalEnergyColumn[state],
                      data: allData[state],
                      component: totalEnergyColumn[state]
                  };
              });

              buildStructureTree(columnsData[currentState], totalEnergyColumn[currentState], currentState);
              tabs.style.display = 'flex'; // Tabs anzeigen
              changeState(currentState); // Wechseln zum hochgeladenen Zustand
          }
      })
      .catch(error => {
          console.error('Error:', error); // Protokolliert den Fehler in der Konsole
          alert('Error uploading file'); // Zeigt eine Fehlermeldung an
      });
  });

  function buildStructureTree(columns, totalEnergyColumn, state) {
      console.log(`Building structure tree for state: ${state}`); // Debugging
      var componentList = document.getElementById('component-list');
      componentList.innerHTML = '';

      // Maschine (Gesamtenergie) hinzufügen
      var machineLi = document.createElement('li');
      var machineInput = document.createElement('input');
      machineInput.type = 'text';
      machineInput.value = 'Maschine (Gesamtenergie)';
      machineInput.readOnly = true;
      machineLi.appendChild(machineInput);
      machineLi.addEventListener('click', function () {
          updateCharts(totalEnergyColumn, columns, totalEnergyColumn, state);
      });
      componentList.appendChild(machineLi);

      // Komponenten hinzufügen
      var componentUl = document.createElement('ul');
      columns.forEach(function (col, index) {
          if (index > 0 && col !== totalEnergyColumn && col !== 'Sonstige [W]') { // Überspringt die Zeit-Spalte und Gesamtenergiespalte
              var li = document.createElement('li');
              var input = document.createElement('input');
              input.type = 'text';
              input.name = 'column-' + index;
              input.value = col;
              input.addEventListener('change', function () {
                  var oldName = columns[index];
                  var newName = input.value;
                  columns[index] = newName; // Aktualisiert den Spaltennamen
                  if (dataStore[state] && dataStore[state].columns) {
                      dataStore[state].columns[index] = newName;
                      // Spaltennamen im DataFrame ändern
                      allData[state][newName] = allData[state][oldName];
                      delete allData[state][oldName];
                      updateCharts(newName, columns, totalEnergyColumn, state);
                  }
              });

              var deleteButton = document.createElement('button');
              deleteButton.textContent = 'Löschen';
              deleteButton.className = 'btn btn-primary'; // Einheitlicher Stil
              deleteButton.style.marginLeft = '10px'; // Abstand zum Eingabefeld
              deleteButton.addEventListener('click', function () {
                  li.remove();
                  var colIndex = columns.indexOf(col);
                  delete allData[state][col];
                  columns.splice(colIndex, 1);
                  if (dataStore[state] && dataStore[state].columns) {
                      dataStore[state].columns.splice(colIndex, 1);
                  }
                  console.log('Remaining Data:', allData);
                  updateCharts(totalEnergyColumn, columns, totalEnergyColumn, state);
              });

              li.appendChild(input);
              li.appendChild(deleteButton);
              li.addEventListener('click', function () {
                  updateCharts(col, columns, totalEnergyColumn, state);
              });
              componentUl.appendChild(li);
          }
      });

      // "Sonstige [W]" hinzufügen (nur einmal)
      var otherLiExists = false;
      componentUl.childNodes.forEach(function (li) {
          if (li.firstChild && li.firstChild.value === 'Sonstige [W]') {
              otherLiExists = true;
          }
      });

      if (!otherLiExists) {
          var otherLi = document.createElement('li');
          var otherInput = document.createElement('input');
          otherInput.type = 'text';
          otherInput.value = 'Sonstige [W]';
          otherInput.readOnly = true;
          otherLi.appendChild(otherInput);

          var deleteButton = document.createElement('button');
          deleteButton.textContent = 'Löschen';
          deleteButton.className = 'btn btn-primary'; // Einheitlicher Stil
          deleteButton.style.marginLeft = '10px'; // Abstand zum Eingabefeld
          deleteButton.addEventListener('click', function () {
              otherLi.remove();
              delete allData[state]['Sonstige [W]'];
              columns.splice(columns.indexOf('Sonstige [W]'), 1);
              if (dataStore[state] && dataStore[state].columns) {
                  dataStore[state].columns.splice(columns.indexOf('Sonstige [W]'), 1);
              }
              console.log('Remaining Data:', allData);
              updateCharts(totalEnergyColumn, columns, totalEnergyColumn, state);
          });

          otherLi.appendChild(deleteButton);
          otherLi.addEventListener('click', function () {
              updateCharts('Sonstige [W]', columns, totalEnergyColumn, state);
          });
          componentUl.appendChild(otherLi);
      }

      componentList.appendChild(componentUl);
  }

  function updateCharts(component, columns, totalEnergyColumn, state) {
      console.log(`Updating charts for component: ${component} in state: ${state}`); // Debugging: Anzeigen, welche Komponente und welcher Zustand aktualisiert wird

      // Debugging: Prüfen der Daten in allData
      console.log(`All Data for state ${state}:`, allData[state]);

      var labels = allData[state][columns[0]]; // Zeiteinheiten aus der ersten Spalte
      var selectedData = allData[state][component]; // Bereits konvertierte numerische Daten

      console.log('Labels:', labels); // Debugging: Anzeigen der Labels
      console.log('Selected Data:', selectedData); // Debugging: Anzeigen der ausgewählten Daten

      if (!labels || !selectedData) {
          console.error('Labels or selected data are missing.'); // Fehlerbehebung, falls Daten fehlen
          return;
      }

      chartTitle.style.display = 'block';

      // Aktualisiere das Liniendiagramm
      var energyChart = Chart.getChart('energyChart');
      if (!energyChart) {
          var ctxLine = document.getElementById('energyChart').getContext('2d');
          energyChart = new Chart(ctxLine, {
              type: 'line',
              data: {
                  labels: labels,
                  datasets: [{
                      label: component,
                      data: selectedData,
                      borderColor: '#C1D100', // Neue Farbe
                      backgroundColor: 'rgba(193, 209, 0, 0.5)',
                      pointRadius: 0, // Entfernt die Punkte aus dem Liniendiagramm
                      fill: false // Nur Linien, kein Füllbereich
                  }]
              },
              options: {
                  responsive: true,
                  maintainAspectRatio: false,
                  scales: {
                      x: {
                          title: {
                              display: true,
                              text: 'Zeit [s]'
                          }
                      },
                      y: {
                          title: {
                              display: true,
                              text: 'Leistung (W)'
                          }
                      }
                  }
              }
          });
      } else {
          energyChart.data.labels = labels;
          energyChart.data.datasets = [{
              label: component,
              data: selectedData,
              borderColor: '#C1D100', // Neue Farbe
              backgroundColor: 'rgba(193, 209, 0, 0.5)',
              pointRadius: 0, // Entfernt die Punkte aus dem Liniendiagramm
              fill: false // Nur Linien, kein Füllbereich
          }];
          energyChart.update();
      }

      // Wenn "Maschine (Gesamtenergie)" ausgewählt ist, aktualisiere auch das Tortendiagramm
      if (component === totalEnergyColumn) {
          pieChartTitle.style.display = 'block';
          pieCanvas.style.display = 'block';
          var otherComponents = columns.filter(key => key !== columns[0] && key !== totalEnergyColumn);
          var pieData = otherComponents.map(comp => {
              if (!allData[state][comp]) {
                  return 0;
              }
              var average = allData[state][comp].reduce((acc, val) => acc + val, 0) / allData[state][comp].length;
              var totalAverage = allData[state][totalEnergyColumn].reduce((acc, val) => acc + val, 0) / allData[state][totalEnergyColumn].length;
              return (average / totalAverage * 100).toFixed(1);
          });

          var energyPieChart = Chart.getChart('energyPieChart');
          if (!energyPieChart) {
              var ctxPie = document.getElementById('energyPieChart').getContext('2d');
              energyPieChart = new Chart(ctxPie, {
                  type: 'pie',
                  data: {
                      labels: otherComponents,
                      datasets: [{
                          data: pieData,
                          backgroundColor: [
                              'rgba(0, 113, 185, 0.5)',
                              'rgba(0, 174, 104, 0.5)',
                              'rgba(255, 159, 0, 0.5)',
                              'rgba(255, 99, 132, 0.5)',
                              'rgba(54, 162, 235, 0.5)',
                              'rgba(75, 192, 192, 0.5)',
                              'rgba(153, 102, 255, 0.5)',
                              'rgba(255, 159, 64, 0.5)'
                          ]
                      }]
                  },
                  options: {
                      responsive: true,
                      maintainAspectRatio: false
                  }
              });
          } else {
              energyPieChart.data.labels = otherComponents;
              energyPieChart.data.datasets[0].data = pieData;
              energyPieChart.update();
          }
      } else {
          pieChartTitle.style.display = 'none';
          pieCanvas.style.display = 'none';
      }
  }

  // Funktion zum Generieren der PDF
  document.getElementById('generate-pdf').addEventListener('click', function() {
      // Show modal for PDF filename input
      var pdfModal = document.getElementById('pdfModal');
      pdfModal.style.display = 'block';

      // Close modal when clicking on <span> (x)
      document.querySelector('.close').onclick = function() {
          pdfModal.style.display = 'none';
      };

      // Close modal when clicking outside of the modal
      window.onclick = function(event) {
          if (event.target == pdfModal) {
              pdfModal.style.display = 'none';
          }
      };

      // Confirm PDF filename and generate PDF
      document.getElementById('confirm-pdf-filename').onclick = function() {
            var pdfModal = document.getElementById('pdfModal');
            pdfModal.style.display = 'none';
            var pdfFilename = document.getElementById('pdf-filename-input').value;

          // Collect machine information
          const machineInfo = {
              company: document.getElementById('company').value,
              model: document.getElementById('model').value,
              location: document.getElementById('location').value,
              date: document.getElementById('date').value,
              time: document.getElementById('time').value
          };

          // Collect percentage values
          const percentages = {
                standby: document.getElementById('standby-percentage').value,
                ready: document.getElementById('ready-percentage').value,
                process: document.getElementById('process-percentage').value
            };

          // Create a FormData object to handle file uploads
          const formData = new FormData();
          formData.append('machine_info', JSON.stringify(machineInfo));
          formData.append('percentages', JSON.stringify(percentages));
          formData.append('file_standby', document.getElementById('file-upload-standby').files[0]);
          formData.append('file_ready', document.getElementById('file-upload-ready').files[0]);
          formData.append('file_process', document.getElementById('file-upload-process').files[0]);
          formData.append('pdf_filename', pdfFilename);

          console.log("Sending PDF generation request.");  // Debugging

          // Send a request to the server to generate the PDF
          fetch('/generate_pdf', {
              method: 'POST',
              body: formData
          })
          .then(response => response.blob())
          .then(blob => {
              // Create a link to download the PDF
              const url = window.URL.createObjectURL(blob);
              const a = document.createElement('a');
              a.style.display = 'none';
              a.href = url;
              a.download = pdfFilename; // Use the entered filename
              
              // Append the link to the document and programmatically click it
              document.body.appendChild(a);
              a.click();
              
              // Clean up
              window.URL.revokeObjectURL(url);
              document.body.removeChild(a);

              pdfModal.style.display = 'none';  // Hide the modal after downloading the PDF
          })
          .catch(error => {
              console.error('Error generating PDF:', error);  // Debugging
          });
      };


      
  });
});

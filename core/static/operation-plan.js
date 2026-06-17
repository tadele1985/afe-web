var getUrlParameter = function getUrlParameter(sParam) {
  var sPageURL = window.location.search.substring(1),
      sURLVariables = sPageURL.split('&'),
      sParameterName,
      i;

  for (i = 0; i < sURLVariables.length; i++) {
      sParameterName = sURLVariables[i].split('=');

      if (sParameterName[0] === sParam) {
          return sParameterName[1] === undefined ? true : decodeURIComponent(sParameterName[1]);
      }
  }
  return false;
};

document.addEventListener("DOMContentLoaded", async () => {
  const data = await fetch(`/api/operation_plans?plan_type=${getUrlParameter("plan_type")}`);
  const resp = await data.json();

  if (!resp) {
    return;
  }

  const headers = Object.keys(resp[0]).splice(1);
  const tmpData = resp.map((obj) => Object.values(obj));
  const tableData = resp.map((obj) => Object.values(obj).splice(1));

  const dataTable = new window.simpleDatatables.DataTable("#plans-table", {
    data: {
      headings: headers,
      data: tableData,
    },
    columns: [
      {
        select: headers.length - 1,
        render: (data, cell, _dataIndex, _cellIndex) => {
          const tableData = tmpData[_dataIndex][0];
          return `<div class="flex gap-2 items-center justify-center"><p>${data[0].data}</p><a hx-boost="true" class="font-medium text-blue-600 hover:underline cursor-pointer" href="${tableData}/">Detail</a></div>`;
        },
      },
    ],
  });

  let sector_filter = document.getElementById("sector_filter")

  if(sector_filter.value != "") {
    dataTable.search(sector_filter.options[sector_filter.selectedIndex].text, [1]);
  }

  document.getElementById("year_filter").addEventListener("change", function() {
    if(this.value != "") {
      dataTable.search(this.options[this.selectedIndex].text, [0]);
    }
  });

  document.getElementById("operations_filter").addEventListener("change", function() {
    if(this.value != "") {
      dataTable.search(this.options[this.selectedIndex].text, [2]);
    }
  });

  document.getElementById("sector_filter").addEventListener("change", function() {
    if(this.value != "") {
      dataTable.search(this.options[this.selectedIndex].text, [1]);
    }
  });
});

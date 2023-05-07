$(document).ready(function() {
  $("#search-navbar").on("input", function() {
    var query = $(this).val();
    
    if (query.length > 2) {
      $.ajax({
        url: "/livesearch",
        data: { q: query },
        dataType: "json",
        success: function(data) {
          displayResults(data);
        }
      });
    } else {
      $("#search-results").hide();
    }
  });
});

function displayResults(data) {
  var resultsContainer = $("#search-results");
  resultsContainer.empty();
  
  var allResults = [].concat(data.result_culturel, data.result_media, data.result_transmedia);
  allResults.forEach(function(result) {
    var resultItem = $("<div>").addClass("search-result-item");
    var title = $("<h4>").text(result.nom);
    resultItem.append(title);
    
    if (result.synopsis) {
      var synopsis = $("<p>").text(result.synopsis);
      resultItem.append(synopsis);
    }
    
    resultsContainer.append(resultItem);
  });

  if (allResults.length > 0) {
    resultsContainer.show();
  } else {
    resultsContainer.hide();
  }
}

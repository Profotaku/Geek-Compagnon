$(document).ready(
  function () {
    $('#search-navbar').on(
      'input',
      function () {
        var query = $(this).val();
        if (query.length > 3) {
          $.ajax({
            url: '/livesearch',
            data: {
              q: query
            },
            dataType: 'json',
            success: function (data) {
              displayResults(data);
            }
          });
        } else {
          $('#search-results').addClass('hidden');
        }
      }
    );
  }
);
function displayResults(data) {
  var resultsContainer = $('#search-results');
  resultsContainer.empty();
  var allResults = [].concat(
    data.result_culturel,
    data.result_media,
    data.result_transmedia
  );
  allResults.forEach(
    function (result) {
      var resultItem = $('<div>').addClass(
        'search-result-item hover:bg-red-600 mb-1 cursor-pointer m-2'
      );
      if (result.url_image) {
        var image = $('<img>').attr('src', result.url_image);
        image.addClass('w-6 h-10 object-cover')
        resultItem.append(image);
      }
      var title = $('<h4>').text(result.nom);
      resultItem.append(title);
      if (result.synopsis) {
        var troncateSynopsis = result.synopsis.substring(0, 150);
        var synopsis = $('<p>').text(troncateSynopsis + '...');
        resultItem.append(synopsis);
      }
      var troncateSynopsis = result.synopsis.substring(0, 150);
      resultsContainer.append(
        `<div class="search-result-item hover:bg-chartpink-400 min-w-full p-2">
                    <a href="#" class="w-full flex inline-flex no-underline text-gray-800">
                        <img src="
        ` + result.url_image + `" class="w-12 h-20 object-cover">
                        <div class="pl-2">
                            <span class="items-baseline">
        ` + result.nom + `</span>
                            <p class="text-sm italic">
        ` + troncateSynopsis + `[...]</p>
                        </div>
                    </a>
                </div>
        `
      )
    }
  );
  if (allResults.length > 0) {
    console.log('result');
    resultsContainer.show();
  } else {
    console.log('no result');
    resultsContainer.hide();
  }
}

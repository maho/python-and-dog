INDEX = """
<!doctype html>
<html lang="en">
  <head>
    <!-- Required meta tags -->
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">

    <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.0-beta3/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-eOJMYsd53ii+scO/bJGFsiCZc+5NDVN2yr8+0RDqr0Ql0h+rP48ckxlpbzKgwra6" crossorigin="anonymous">
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>

    <title>Treat your dog v2.0.1</title>
  </head>
  <body>
    <h1>Treat your dog v2.0.1 </h1>
	<div class='container'>
            <div class='col-6'>
                Reward your dog:
            </div>
            <button class='btn btn-primary col-sm-12 col-lg-2' name='portion' value='1'>SMALL</button>
            <button class='btn btn-secondary col-sm-12 col-lg-2' name='portion' value='2'>MEDIUM</button>
            <button class='btn btn-primary col-sm-12 col-lg-2' name='portion' value='3'>BIG</button>
            <button class='btn btn-primary col-sm-12 col-lg-2' name='portion' value='-1'>BACK</button>
    </div>

    <!-- Optional JavaScript -->
    <!-- jQuery first, then Popper.js, then Bootstrap JS -->

    <script>
        $("button[name=portion]").click(function() {
            var portion=$(this).attr("value")

            var data = JSON.stringify({"portion": portion})
            $.post({url: "/treat",
                    contentType: "application/json"},
                   data)

        })
    </script>

  </body>
</html>
"""


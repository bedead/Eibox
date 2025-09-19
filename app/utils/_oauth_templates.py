"""
HTML & CSS Templates for rendering GMAIL OAUTH success and error data.
"""

CALLBACK_SUCCESS_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Gmail Connected</title>
  <style>
    body {
      font-family: Arial, sans-serif;
      background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
      color: #333;
      display: flex;
      justify-content: center;
      align-items: center;
      height: 100vh;
      margin: 0;
    }
    .container {
      background: #fff;
      border-radius: 16px;
      padding: 40px 30px;
      text-align: center;
      box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
      max-width: 400px;
      width: 100%;
    }
    h2 {
      color: #28a745;
      margin-bottom: 20px;
    }
    p {
      margin: 8px 0;
      font-size: 16px;
    }
    .icon {
      font-size: 50px;
      margin-bottom: 10px;
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="icon">✅</div>
    <h2>Gmail Connected!</h2>
    <p><strong>Username:</strong> {{username}}</p>
    <p><strong>Email:</strong> {{email}}</p>
  </div>
</body>
</html>
"""

CALLBACK_ERROR_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Error</title>
  <style>
    body {
      font-family: Arial, sans-serif;
      background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%);
      color: #333;
      display: flex;
      justify-content: center;
      align-items: center;
      height: 100vh;
      margin: 0;
    }
    .container {
      background: #fff;
      border-radius: 16px;
      padding: 40px 30px;
      text-align: center;
      box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
      max-width: 400px;
      width: 100%;
    }
    h2 {
      color: #dc3545;
      margin-bottom: 20px;
    }
    p {
      margin: 8px 0;
      font-size: 16px;
    }
    .icon {
      font-size: 50px;
      margin-bottom: 10px;
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="icon">❌</div>
    <h2>Error</h2>
    <p>{{error}}</p>
  </div>
</body>
</html>
"""

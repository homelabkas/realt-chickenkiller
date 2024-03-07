# Run the application using python

  

install the dependancies

    pip install flask
    pip install "flask[async]"
    pip install requests
    pip install gevent

run the application

    python app.py

  
Open your browser on port 8080

http://localhost:8080/

  
  

# Run the application using docker

  

Build the image

    docker build -t realt1234-chickenkiller:v1 .`

  

run the image

    docker run -d -p 8080:8080 realt1234-chickenkiller:v1

  
Open your browser on port 8080

http://localhost:8080/


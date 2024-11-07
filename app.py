from flask import Flask, render_template, request, jsonify
import requests
import json
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)
apikey = "71ef5f1"

# Caché para banderas de países
country_flags_cache = {}

def searchfilms(search_text):
    url = f"https://www.omdbapi.com/?s={search_text}&apikey={apikey}&page=1"
    response = requests.get(url)
    if response.status_code == 200:
        results = response.json()
        # Limita a 10 resultados para mejorar el rendimiento
        results["Search"] = results.get("Search", [])[:10]
        return results
    else:
        print("Failed to retrieve search results.")
        return None
    
def getmoviedetails(movie):
    url = f"https://www.omdbapi.com/?i={movie['imdbID']}&apikey={apikey}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print("Failed to retrieve movie details.")
        return None

def get_country_flag(fullname):
    if fullname in country_flags_cache:
        return country_flags_cache[fullname]

    url = f"https://restcountries.com/v3.1/name/{fullname}?fullText=true"
    response = requests.get(url)
    if response.status_code == 200:
        country_data = response.json()
        if country_data:
            flag_url = country_data[0].get("flags", {}).get("svg", None)
            country_flags_cache[fullname] = flag_url
            return flag_url
    print(f"Failed to retrieve flag for country: {fullname}")
    return None

def merge_data_with_flags(filter):
    filmssearch = searchfilms(filter)
    if filmssearch is None or "Search" not in filmssearch:
        return []
    
    moviesdetailswithflags = []
    
    # Usamos ThreadPoolExecutor para obtener detalles de películas en paralelo
    with ThreadPoolExecutor() as executor:
        movie_details = list(executor.map(getmoviedetails, filmssearch["Search"]))
        
        for moviedetails in movie_details:
            if moviedetails is None or "Country" not in moviedetails:
                continue
            
            countriesNames = moviedetails["Country"].split(",")
            countries = []
            
            for country in countriesNames:
                country_name = country.strip()
                countrywithflag = {
                    "name": country_name,
                    "flag": get_country_flag(country_name)  # Utiliza caché para banderas
                }
                countries.append(countrywithflag)
            
            moviewithflags = {
                "title": moviedetails["Title"],
                "year": moviedetails["Year"],
                "countries": countries
            }
            moviesdetailswithflags.append(moviewithflags)

    return moviesdetailswithflags

@app.route("/")
def index():
    filter = request.args.get("filter", "").upper()
    return render_template("index.html", movies=merge_data_with_flags(filter))

@app.route("/api/movies")
def api_movies():
    filter = request.args.get("filter", "")
    return jsonify(merge_data_with_flags(filter))    

if __name__ == "__main__":
    app.run(debug=True)

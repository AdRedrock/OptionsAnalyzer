# 📈 Options Analyzer in a nutshell

**Options Analyzer** is a Python-based software application, designed to analyze the options market. It is aimed at teachers, enthusiasts and individuals wishing to learn about these markets.

Access to historical options market data is often **unavailable or expensive**. That's why I decided to create my own software, incorporating the **pre-designed analysis tools** I'm sharing with you today.

With **Options Analyzer**, you can **create your own database** and **study the options market in greater depth** to better understand the issues.

| ![](/screenshots/screenshot1.png) | ![](/screenshots/screenshot2.png) |
|-----------------------------------|-----------------------------------|
| ![](/screenshots/screenshot3.png) | ![](/screenshots/screenshot4.png) |


# 🔍 Features

✅ **Volume & Open Interest Analysis**  
   - Visualize volume and OI by strike price  
   - Identify expirations with the highest open interest and trading volume  
   - Compare different imported datasets  

✅ **IV Indicators**  
   - Compare **Implied Volatility (IV) vs. Realized Volatility**  
   - Analyze **25-Delta Skew** & **Butterfly Delta Skew**  
   - Generate **Volatility Smiles** with multiple data processing algorithms  
   - Display **IV Surface**  

✅ **Options Greeks**  
   - **Gamma Exposure (GEX)**  
   - **Delta Exposure (DEX)**  
   - **Vanna Exposure (VEX)**  

✅ **Options Payoff Analysis**  
   - Model simple and complex strategies  
   - Run **Monte Carlo simulations**  
   - Display key statistics  

✅ **Customizable Data Filtering**  
   - Filter by **strike price, expiration date, moneyness,** and more!  

All this while being able to apply filters such as strike range, expiration, moneyness, etc.

# 🛠 Installation

### ⚠ After conducting several tests on VirusTotal, it is recommended to disable or add an exception for ESET NOD and Ikarus antivirus software.

1. **Download the installer** and run it.  
2. **Follow the instructions** in the setup file.  
3. Once installed, **run `OptionsAnalyzer.exe`**.   


✅ **Compatibility** : Windows 64-bits for now, all platforms from source code


## ℹ General information

The payoff displayed is based solely on premiums and the price of the underlying at a given expiration, without taking into account the time evolution of options with different maturities.
It is therefore not currently possible to study diagonal strategies.


### 📊 Select Expiration (Select Expiration drop-down lists)

These are the types of selections -> All, Peak, Specific, Custom Selection

| Option       | Description |
|-------------|------------|
| **All**     | Takes all deadlines into account. |
| **Peak**    | Defines a maximum expiry. |
| **Specific** | Select expiry one by one. |
| **Custom Selection** | Allows you to choose your own pre-set options. |


# 👤 About me 

🎓 I am a Master's student in Finance. Through this project, I wanted to pass on my passion for financial markets, trading and investing.

💻 I'm not a **professional developer, just an enthusiast**, nor am I a financial professional or **mathematician/statistician**. 

⚠ Software limitations

🔹 Certain **technical constraints** can affect the accuracy of calculations.

🔹 Intraday data can only be imported for a maximum period of 60 days (Yahoo Finance limitation). 


# 💡 Contribute to the project


✅ Would you like to contribute? Here are a few ideas:

* Improve calculation methods, taking into account data limitations.
* Add new indicators or features.
* Create a new logo (graphic designers beware! 🎨).
* Optimize the user interface to make it more intuitive.

💖 Support me with a coffee ☕ : [buymeacoffee](https://buymeacoffee.com/adredrock)

# 🚀 Future projects

* Integrate more options markets (currently, only CBOE options are available).
* Add options on futures, bonds and cryptocurrencies...
* Implement diagonal strategy calculations.
* Automate data import at a specific time for a specific market.
* Implement an SQL database for improved data management.

# ⚠ Disclaimer

This is a free project. This means it relies on publicly available data.
Consequently, some indicators, particularly in the “IV indicators” section, may not be suitable for less liquid assets, or for assets with option maturities that are too far apart.

🔗 I invite you to read the doc inside the project to find out more about the calculation methods for each indicator and their limits.

I am in no way responsible for your use of this software. This software is intended primarily for educational purposes.
As such, I am in no way responsible for your analyses, or for your financial losses.

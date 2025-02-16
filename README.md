# 📈 Options Analyzer Project

Welcome to the **Options Analyzer** project !   


🔗 **Link to the GitHub project (desktop version)** : [Options Analyzer](https://github.com/AdRedrock/OptionsAnalyzer)  

This README serves as **mini a documentation** to help those who wish to **understand the project** or **contribute to its development**.

💖 If you would like to support this project ☕, you can [buymeacoffee](https://buymeacoffee.com/adredrock)

---

# 🛠 Installation

### 1️. Clone the repository :
 
   `git clone https://github.com/AdRedrock/options-analyzer-dev.git` 

### 2. Create the python environment :

`python -m venv .env`. 

### 3. Activate the environment :

    (linux) source .env/bin/activate

    (windows) .env\Scripts\activate


### 4. Once the environment is activated, run :

    pip install -e . 

### 5. Launch the program :

#### 🌐 Web Version (Recommended for development)

    python webapp.py

   * Accessible by default at : https://127.0.0.1:8050

#### 🖥️ Desktop Version

     python OptionsAnalyzer.py

# Options Analyzer – Technical documentation

## 📌 General Information and Project Structure

Options Analyzer is a software application built with **Dash (Flask)**, integrating a **callbacks** system for dynamic interaction management.  
The **desktop** version is a **web application embedded** in **PySide6**.

### 📂 Project Structure
- **`data/`** : Directory used to store imported data. The program loads this data for subsequent analysis.
- **`src/analyzers/`** : Contains the scripts responsible for metrics, payoff calculation and data filtering.
- **`src/gui/`** : Contains the Dash user interface and callbacks.
- **`src/system/`** : Management of desktop features and import paths to avoid circular imports.

### 🌍 Time Zone Management
- By default, data is **standardized to UTC+1**.
- The program **dynamically converts** data according to the time zone selected by the user.

---

## 📊 Indicator calculations

### 🔹 Data restrictions
Certain constraints linked to data sources influence the calculation of indicators:
- **IV vs Realized Volatility** :
  - An **interpolation** is performed between the first maturity under 30 days and the first maturity over 30 days, to maximize asset coverage.
  - **yFinance limitation**: Intraday candles are only available for 60 days**, which prevents accurate calculation of intraday volatility.

### 🔹 Vanna calculation
- The **risk-free interest rate** used to calculate options **is not provided by CBOE**.
- The program uses the ticker **`^IRX` (13 Week Treasury Bill)**.
- The risk-free rate is recalculated using the **Black-Scholes model**, **without accounting for dividends.**.

---

If you have suggestions for optimizations, please let us know.

---

## 🛠 Contributions and Improvements
If you would like to contribute :
1. Fork the repository.
2. Propose improvements and submit a **Pull Request**.
3. If you have suggestions to optimize calculations, open an **Issue**.

---

📜 **License** : _(Apache 2.0)_

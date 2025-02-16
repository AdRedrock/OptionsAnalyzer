import yfinance as yf
import numpy as np
import pandas as pd

import plotly.graph_objects as go

from src.import_data.utils import LoadingData

class GetDataAndCalculation:

    def __init__(self):

        self.class_LoadingData = LoadingData()

    def get_st_mu_sig(self, start_date, end_date, selected_option):

        st, change, quotation_type, quotation_value,lot_size = self.class_LoadingData.load_st_ticker_info_json(provider='search', selected_option=selected_option)

        data = yf.download(st, start=start_date, end=end_date, interval='1d')

        business_days = len(pd.date_range(start=start_date, end=end_date, freq='B'))

        data['variation'] = np.log(data['Close'] / data['Close'].shift(1))

        mu_daily = data['variation'].mean()
        annualized_mu = mu_daily * 252

        sig_daily = data['variation'].std()

        if business_days > 252:
            annualized_sig = sig_daily * np.sqrt(252)

        elif business_days <= 252:
            annualized_sig = sig_daily * np.sqrt(252)

        return annualized_mu, annualized_sig
    
    @staticmethod
    def get_time(time_str, df):


        if '1w' in time_str:
            return 5
        
        if '2w' in time_str:
            return 10
        
        if '1mo' in time_str:
            return 21
        
        if '3mo' in time_str:
            return 63
        
        if '6mo' in time_str:
            return 126
        
        if '1y' in time_str:
            return 252
        
        if '2y' in time_str:
            return 730

        if 'min' in time_str:
            min_days = min(int(d['maturity'].split()[0]) for d in df)

            return min_days
            
        if 'max' in time_str:
            max_days = max(int(d['maturity'].split()[0]) for d in df)
    
            return max_days
        


class Simulation:
    def __init__(self, selected_option, df, nbr_sim, mu, sig, time, plot=True):

        if isinstance(mu, str):
            mu_cleaned = mu.strip().replace("%", "")
        else:
            mu_cleaned = str(mu)

        if isinstance(sig, str):
            sig_cleaned = sig.strip().replace("%", "")
        else:
            sig_cleaned = str(sig)

        self.df = df
        self.time = time
        self.selected_option = selected_option
        self.nbr_sim = int(nbr_sim)
        self.mu_float = float(mu_cleaned) / 100
        self.sig_float = float(sig_cleaned) / 100
        self.plot = plot

        result = GetDataAndCalculation().get_time(self.time, self.df)

        self.mu = self.mu_float * (result/252)
        self.sig = self.sig_float * np.sqrt(result/252)

        self.T = int(result)
        self.n_steps = 1

        print(self.mu_float)
        print(self.sig_float)

        print(self.mu)
        print(self.sig)
        self.class_ = PayoffFormula(self.df, self.selected_option)
        self.class_plot = PlotMonteCarlo()

        self.St = self.class_.getLastSt()

        self.monteCarlo()
        self.monteCarloDistrib()


    def monteCarlo(self):

        S0 = self.St
        dt = self.n_steps / self.T  
        n_steps = self.T
        paths = np.zeros((self.nbr_sim, n_steps))
        
        drift = (self.mu - 0.5 * self.sig**2) * dt
        diffusion = self.sig * np.sqrt(dt)

        Z = np.random.normal(0, 1, (self.nbr_sim, n_steps))
        exp_factor = np.exp(drift + diffusion * Z)

        paths[:, 0] = S0
        for t in range(1, n_steps):
            paths[:, t] = paths[:, t - 1] * exp_factor[:, t]

        payoffs = np.vectorize(self.class_.payoff)(paths)

        self.df_simulation = pd.DataFrame(payoffs.T, columns=[f'{i+1}' for i in range(self.nbr_sim)])
      
        if self.plot:
            self.figure2 = self.class_plot.plotSimTrack(self.df_simulation)
        
        return self.df_simulation
    
    def monteCarloDistrib(self):
      
        self.final_values = self.df_simulation.iloc[-1]

        distribution_stats = {
            "Mean": self.final_values.mean(),
            "StdDev": self.final_values.std(),
            "5th Percentile": self.final_values.quantile(0.05),
            "50th Percentile (Median)": self.final_values.median(),
            "95th Percentile": self.final_values.quantile(0.95)
        }

        self.mean = self.final_values.mean()
        self.std = self.final_values.std()
        self.percentile_5 = self.final_values.quantile(0.05)
        self.percentile_95 = self.final_values.quantile(0.95)
        self.median = self.final_values.median()

        if self.plot:
            self.figure1, self.max_prob, self.max_prob_range, self.min_prob, self.min_prob_range, self.max_payoff, self.min_payoff, self.max_payoff_prob, self.min_payoff_prob, self.positive_payoff, self.negative_payoff= self.class_plot.plotSimDistrib(self.final_values, distribution_stats)

        return pd.DataFrame([distribution_stats])

class PlotMonteCarlo:

    def __init__(self):
        pass

    def plotSimTrack(self, df):

        fig = go.Figure()
        i = 0
        for col in df.columns:
            i = i + 1
            fig.add_trace(go.Scatter(
                x=df.index,
                y=df[col],
                mode='lines',
                name=f'Simulation {i}'
            ))
        
        fig.update_layout(
            title=f"Monte Carlo Trajectories",
            xaxis_title="Time",
            yaxis_title=f"Option(s) Payoff Value",
            template="plotly_white",
            dragmode=False,
            showlegend=False,
            xaxis=dict(
                fixedrange=True,
            ),
            yaxis=dict(
                fixedrange=True,
            ),
        )
        
        return fig


    def plotSimDistrib(self, final_values, stats):
  
        if len(final_values) == 0:
            print("Error: final_values is empty.")
            return

        nb_bins = int(np.sqrt(len(final_values))) * 10

        print(f' Range des BINS {nb_bins}')

        bin_width = nb_bins
        bins = np.arange(final_values.min(), final_values.max() + bin_width, bin_width)

        hist, bins = np.histogram(final_values, bins=bins, density=False)
        hist = hist / hist.sum()
        bin_centers = (bins[:-1] + bins[1:]) / 2

        bin_ranges = [f"[{bins[i]:.2f}, {bins[i+1]:.2f}]" for i in range(len(bins) - 1)]

        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=bin_centers,
            y=hist,
            name="Payoff Distribution",
            marker=dict(
                color=hist,
                colorscale="Ice",
                showscale=True,
                colorbar=dict(title="Prob. Density")
            ),
            customdata=bin_ranges,  
            hovertemplate="Range: %{customdata}<br>Density: %{y:.4f}<extra></extra>",
            width=(bins[1] - bins[0]) * 0.9
        ))

        max_prob_index = np.argmax(hist)
        min_prob_index = np.argmin(hist)

        max_prob = hist[max_prob_index]
        max_prob_range = (bins[max_prob_index], bins[max_prob_index + 1])

        min_prob = hist[min_prob_index]
        min_prob_range = (bins[min_prob_index], bins[min_prob_index + 1])

        max_payoff = final_values.max()
        min_payoff = final_values.min()

        max_bin_index = np.digitize(max_payoff, bins) - 1
        min_bin_index = np.digitize(min_payoff, bins) - 1

        max_payoff_prob = hist[max_bin_index] if 0 <= max_bin_index < len(hist) else 0
        min_payoff_prob = hist[min_bin_index] if 0 <= min_bin_index < len(hist) else 0

        positive_payoff = (final_values > 0).sum() / len(final_values)
        negative_payoff = (final_values <= 0).sum() / len(final_values)

        print(f'range {max_prob_range} p = {max_prob_index}')

        print(f"Max Probability: {max_prob}")
        print(f"Max Probability Range: {max_prob_range}")

        annotations = [
            {"x": stats["Mean"], "text": "Mean", "color": "blue"},
            {"x": stats["95th Percentile"], "text": "95th Percentile", "color": "red"},
            {"x": stats["50th Percentile (Median)"], "text": "Median", "color": "green"},
            {"x": stats["5th Percentile"], "text": "5th Percentile", "color": "red"},            
        ]

        max_hist_height = max(hist)
        base_height = max_hist_height * 1.2
        spacing = max_hist_height * 0.1

        for i, ann in enumerate(annotations):
            fig.add_shape(
                type="line",
                x0=ann["x"], 
                x1=ann["x"],
                y0=0, 
                y1=base_height,
                line=dict(color=ann["color"], dash="dash")
            )
            
            fig.add_annotation(
                x=ann["x"],
                y=base_height + (i * spacing),  
                text=ann["text"],
                showarrow=False,
                font=dict(color=ann["color"]),
                align="center"
            )


        fig.update_layout(
            title="Distribution of Payoff at the End of Simulation",
            xaxis_title="Payoff",
            yaxis_title="Probability Density",
            template="plotly_white",
            xaxis=dict(range=[bins[0] - nb_bins, bins[-1]], fixedrange=True),
            yaxis=dict(range=[0, base_height + (len(annotations) * spacing) * 1.2], fixedrange=True),
            dragmode=False,
            hovermode="x",
            modebar_add=[
                "v1hovermode",
                "toggleSpikelines",
            ],
        )

        return fig, max_prob, max_prob_range, min_prob, min_prob_range, max_payoff, min_payoff, max_payoff_prob, min_payoff_prob, positive_payoff, negative_payoff
    


class PayoffFormula:
    def __init__(self, df, selected_option):

        self.df = df
        self.selected_option = selected_option

        self.type = []
        self.pos = []
        self.strike = []
        self.premium = []
        self.expiration = []

        self.class_LoadingData = LoadingData()

        self.underlying, self.change, self.quotation_type, self.quotation_value, self.lot_size = self.class_LoadingData.load_st_ticker_info_json(provider='search', selected_option=self.selected_option)

        self.optionToList()


    def payoff(self, St):
        
        returns = []

        for i in range(len(self.type)):

            if self.type[i] == 'call':

                result = self.callPayoff(St, self.pos[i], self.strike[i], self.premium[i])

            if self.type[i] == 'put':
                result = self.putPayoff(St, self.pos[i], self.strike[i], self.premium[i])

            returns.append(result)

        total = sum(returns)

        return total

    def callPayoff(self, St, pos, strike, premium):

        if pos == 'Long':
            payoff = - premium + max(0, St - strike)
        if pos == 'Short':
            payoff = + premium - max(0, St - strike)


        return payoff

    def putPayoff(self, St, pos, strike, premium):

        if pos == 'Long':
            payoff = - premium + max(0, strike - St)
          
        elif pos == 'Short':
            payoff = premium - max(0, strike - St)

        return payoff

    def getLastSt(self):
        st_data = yf.download(self.underlying, period='1d', interval='1m')
        last_st = float(round(st_data['Close'].iloc[-1], 2))

        return last_st

    def optionToList(self):
         
         factor = self.premiumFactor(self.quotation_type, self.quotation_value, self.lot_size)
         
         for i in range(len(self.df)):
           
            self.type.append(str(self.df[i]['type']))
            self.pos.append(str(self.df[i]['pos']))
            self.strike.append(float(self.df[i]['strike']))
            self.premium.append(float(self.df[i]['premium']) * factor)
            self.expiration.append(self.df[i]['maturity'])

    def premiumFactor(self, quotation_type, quotation_value, lot_size):

        if quotation_type == 'direct_quote':
            premium_factor = int(quotation_value) * int(lot_size)

            return premium_factor

        elif quotation_type == 'points':
            premium_factor = int(quotation_value) * int(lot_size)

            return premium_factor

        elif quotation_type == 'nominal_value':
            premium_factor = int(quotation_value)

            return premium_factor 

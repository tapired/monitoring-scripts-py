# Morpho Monitoring

## Governance

For roles on Morpho vaults, refer to the following [document](https://github.com/morpho-org/metamorpho/blob/main/README.md).

Morpho governance monitoring is defined in the [Python script](./governance.py) that is executed hourly via [GitHub Actions](../.github/workflows/hourly.yml).

The script checks if there are any new values pending in the timelock for a given vault. It detects the following changes:

- Changing timelock value, minimal values is 1 day.
- Changing guardian address.
- Changing supply caps, only to higher value than the current one, for both supply and withdraw markets.
- Removing of a market from the vault.

### How to Add a New Vault

Add the vault address to either the `MAINNET_VAULTS` or `BASE_VAULTS` variable in [governance.py#L21](./governance.py#L21) to monitor governance changes.

## Vaults & Markets

Morpho Vaults consist of multiple markets, each defining key parameters such as LTV, interest rate models, and oracle data.

Market monitoring is configured via the vault definitions in [markets.py#L13](./markets.py#L13). The script fetches all markets for each vault and checks the following metrics:

- **Bad Debt Ratio:** If the bad debt ratio exceeds 0.5% of total borrowed assets, a Telegram message is sent.
- **Utilization Ratio:** If the utilization ratio exceeds 95%, a Telegram message is sent.
- **Vault Risk Level:** If the computed risk level of a vault exceeds its maximum threshold, a Telegram message is sent.
- **Market Allocation Ratio:** If any market's allocation ratio exceeds its risk-adjusted threshold, a Telegram message is sent.

Additional insights on Morpho vault risks are available at [Llama Risk blog](https://www.llamarisk.com/research/morpho-vaults-risk-disclaimer).

### Risk Levels

The overall risk level of a Morpho Vault is determined by the risk levels of its markets. For more details, refer to the comments in [markets.py#L36](./markets.py#L36). Markets and vaults are categorized by their risk level and blockchain, with Level 1 representing the safest configuration.

### How to Add a New Vault

To monitor a new Morpho vault, add its address to the `VAULTS_BY_CHAIN` variable in [markets.py#L13](./markets.py#L13). This ensures that both the vault's overall metrics and its individual markets are monitored.

For some chains, the Morpho GraphQL API is not available. In this case, alternative script is used [markets_graph.py](./markets_graph.py) which uses The Graph API. Be aware that this script will require additional setup as it uses a different URL for vaults and markets, depending on the curator and frontend. Also, if the new chain is added, it will need new subgraph url define in [`GRAPH_BY_CHAIN`](./markets_graph.py#L29) variable.

### Bad Debt

Bad debt is fetched from the Morpho GraphQL API. Each market is checked for bad debt; if any market exhibits bad debt, a Telegram message is sent. The script runs hourly via [GitHub Actions](../.github/workflows/hourly.yml). The monitoring logic is implemented in [markets.py#L166](./markets.py#L166).

### Utilization

The utilization ratio for each market is calculated as the ratio of borrowed assets to total collateral assets. If this ratio exceeds 95%, a Telegram message is sent. The script runs hourly via [GitHub Actions](../.github/workflows/hourly.yml), and the monitoring logic is defined in [markets.py#L263](./markets.py#L263). Note that liquidity is the inverse of utilization—high utilization implies low liquidity (e.g., 95% utilization corresponds to 5% liquidity).

### Vault Risk Level

The total risk level of a vault is computed as the weighted sum of the risk levels of its individual market allocations:

```math
\text{Total Risk Level} = \sum_{i=1}^{n} (\text{Market Risk Level}_i \times \text{Allocation}_i)
```

Where:

- **Market Risk Level:** A value between 1 and 5, with 1 representing the lowest risk. This value acts as a multiplier (e.g., a market with risk level 1 contributes a multiplier of 1, level 2 contributes 2, etc.).
- **Allocation:** The percentage of the vault's assets allocated to that market.
- **Total Risk Level:** The sum of the weighted risks across all markets.

This computed risk level is compared against predefined maximum thresholds defined in [markets.py#L134](./markets.py#L134):

- **Risk Level 1:** Maximum threshold of 1.10
- **Risk Level 2:** Maximum threshold of 2.20
- **Risk Level 3:** Maximum threshold of 3.30
- **Risk Level 4:** Maximum threshold of 4.40
- **Risk Level 5:** Maximum threshold of 5.00

If a vault's total risk level exceeds its threshold, an alert is triggered via a Telegram message.

### Market Allocation Ratio

The system monitors each market's allocation within a vault to ensure it does not exceed its risk-adjusted threshold. Each market has a maximum allocation threshold based on its inherent risk tier and the vault's overall risk level.

The base allocation limits by risk tier (as defined in [markets.py#L125](./markets.py#L125)) are:

- **Risk Level 1:** 100%
- **Risk Level 2:** 30%
- **Risk Level 3:** 10%
- **Risk Level 4:** 5%
- **Risk Level 5:** 1%

These limits apply to vaults with a risk level of 1. For vaults with higher risk levels, the thresholds become more permissive. The adjustment is calculated in the [get_market_allocation_threshold](./markets.py#L143) function.

Examples:

- A Risk-1 vault accepts up to 30% of its total assets in a Risk-2 market.
- A Risk-2 vault accepts up to 80% of its total assets in a Risk-2 market.
- A Risk-3 vault accepts up to 100% of its total assets in a Risk-2 market.
- A Risk-2 vault accepts up to 10% of its total assets in a Risk-4 market.
- A Risk-3 vault accepts up to 30% of its total assets in a Risk-4 market.

The system monitors the allocation ratio for each market hourly:

```math
\text{Allocation\_ratio} = \frac{\text{Market Supply USD}}{\text{Total Vault Assets USD}}
```

If any market's allocation exceeds its adjusted threshold, an alert is triggered with a corresponding Telegram message. This mechanism ensures that vaults maintain proper diversification and are not overly concentrated in higher-risk markets.

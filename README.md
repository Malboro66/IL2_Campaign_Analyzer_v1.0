# IL-2 Campaign Analyzer

An unofficial desktop application for parsing and analyzing campaign data from Pat Wilson's Campaign Generator (PWCG) for IL-2 Sturmovik.

This tool provides a graphical user interface to visualize your pilot's career, track squadron statistics, view mission logs, and browse notable aces from your campaign.

![Application Screenshot](https://raw.githubusercontent.com/your-repo/your-image.png) <!--- Placeholder for a future screenshot -->

## Features

-   **Campaign Data Visualization**: Load and process data from your PWCG campaign folders.
-   **Pilot & Squadron Dashboard**: View at-a-glance statistics for your pilot and squadron.
-   **Detailed Mission Logs**: Browse a complete history of all missions flown.
-   **Campaign Aces**: See a list of the top-scoring aces in your campaign.
-   **Advanced Notification Viewer**: Filter and search campaign event logs by date, category, keywords, and more.
-   **Plugin Support**: Extend the application's functionality with custom tabs.
-   **Data Export**: Generate `.txt` diaries and detailed PDF reports for missions and statistics.

## Requirements

-   **Python**: 3.8+
-   **Operating System**: Windows, macOS, or Linux
-   **Dependencies**: See `requirements.txt`

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-repo/il2-campaign-analyzer.git
    cd il2-campaign-analyzer
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    # For Windows
    python -m venv venv
    venv\Scripts\activate

    # For macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install the required dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Usage

1.  **Run the application:**
    ```bash
    python main_app.py
    ```

2.  **Select PWCG Folder**:
    -   On first launch, click **"Select PWCGFC Folder"**.
    -   Navigate to your main PWCG installation directory (this is the folder that contains the `User` subfolder). The application will save this path for future sessions.

3.  **Choose a Campaign**:
    -   Use the dropdown menu to select the campaign you wish to analyze.

4.  **Sync Data**:
    -   Click the **"Sincronizar Dados"** (Sync Data) button to load and process all the data for the selected campaign.

5.  **Explore**:
    -   Navigate through the different tabs to view pilot information, mission details, squadron rosters, and more.

## Project Structure

The project is organized into several key modules:

```
.
├── app/
│   ├── core/         # Core logic: data parsing, processing, reporting
│   ├── plugins/      # Directory for custom plugins
│   ├── resoucers/    # Typo: Should be 'resources' (for images, etc.)
│   └── ui/           # UI components (tabs and widgets)
├── main_app.py       # Main application entry point
├── requirements.txt  # Project dependencies
└── README.md         # This file
```

### Data Flow

1.  **`main_app.py`**: Manages the main window, UI controls, and initiates data loading.
2.  **`app/core/data_parser.py`**: Reads and parses the raw `.json` files from the PWCG campaign directory.
3.  **`app/core/data_processor.py`**: Takes the raw data, cleans it, enriches it, and transforms it into a structured format suitable for the UI.
4.  **`app/ui/*.py`**: The various tab widgets receive the processed data and display it to the user.
5.  **`app/core/signals.py`**: A global signal system used to communicate events (like item selection) between different UI components without direct coupling.

## For Developers

### Creating a Plugin

You can extend the application by creating your own tabs.

1.  Create a new Python file in the `app/plugins/` directory (e.g., `my_plugin.py`).
2.  Inside the file, create a `QWidget` subclass for your tab's content.
3.  Implement a function named `register_plugin(tab_manager)`.
4.  Inside this function, call `tab_manager.register_tab("My Tab Name", YourWidgetClass)`.

See `app/plugins/example_tab.py` for a working example.

### Running Tests

(Note: Test framework setup is pending.)

To run the included tests:

```bash
# Placeholder for test execution command
```

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
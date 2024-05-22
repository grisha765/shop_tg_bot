# shop_tg_bot
Telegram bot that manages a product catalog, allowing administrators to add and delete products, and users to browse and purchase them. The bot uses the Pyrogram library for interaction with Telegram and sqlite3 for database management.
### Initial Setup

1. **Clone the repository**: Clone this repository using `git clone`.
2. **Create Virtual Env**: Create a Python Virtual Env `venv` to download the required dependencies and libraries.
3. **Download Dependencies**: Download the required dependencies into the Virtual Env `venv` using `pip`.

```shell
git clone https://github.com/grisha765/shop_tg_bot.git
cd shop_tg_bot
python3 -m venv venv
venv/bin/pip install pyrogram
```

### Run Bot

1. Start an Instance: Start an instance from the venv virtual environment by entering your TOKEN using the -t argument received from @BotFather.

```shell
venv/bin/python main.py -t TOKEN
```

### Arguments

1. **-t, --token**: Required. Specify the Telegram bot token received from @BotFather.

### Features

1. **Product Management**:
    ***Add Products***: Admins can add new products with details such as name, description, quantity, price, and image.
    ***Delete Products***: Admins can delete products from the catalog.
    ***Update Products***: Admins can update product details like quantity and price.

2. **Product Browsing**:
    ***List Products***: Users can browse through a list of available products.
    ***Paginated View***: Products are displayed in a paginated view for easy navigation.
    ***View Product Details***: Users can view detailed information about each product, including images.

3. **Purchase Products**:
    ***Request Purchase***: Users can request to purchase products.
    ***Admin Approval***: Admins receive purchase requests and can approve or reject them.
    ***Notification***: Users receive notifications about the status of their purchase requests.

### Database

1. The bot uses an SQLite database to store product information.
2. The database schema includes fields for product ID, name, description, quantity, and price.

### Example Usage

1. Adding a Product: Admins can add a product by providing the product details and an image.
2. Deleting a Product: Admins can delete a product by its ID.
3. Viewing Products: Users can navigate through the product list and view details of each product.
4. Purchasing a Product: Users can request to purchase a product, and admins can approve or reject the request.

### Dependencies

1. pyrogram: For Telegram API interaction.
2. sqlite3: For database management.

### Notes

1. Ensure that the data directory exists or create it before running the bot.
2. Ensure that you have the required permissions to send messages and media in your Telegram bot.

### Troubleshooting

1. If you encounter any issues, ensure that your dependencies are installed correctly and that your Telegram bot token is valid.
2. Check the console output for any error messages that can help identify the issue.

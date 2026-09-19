# Glossary

- **FoodItem**: A generic, distinct type of food (e.g., "Banana", "Chicken Breast"). Stored in the database with baseline nutritional information (calories per unit/serving).
- **Meal**: A specific instance of food consumption by a user, composed of one or more FoodItems in specific quantities, as identified from a user's uploaded image.
- **MealFood**: One FoodItem within a Meal, as identified from the image: the food's name, the quantity of it, and the calories for that quantity (or none, when the food has no FoodItem baseline in the database).
- **MockAuth**: The simplified authentication mechanism used for the MVP, which allows the frontend to connect without requiring a full user registration/login flow.

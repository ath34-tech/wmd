def test_lists_seeded_food_items_with_baseline_calories(client):
    response = client.get("/api/food-items")

    assert response.status_code == 200
    items = {item["name"]: item for item in response.json()}
    assert items["Banana"]["calories_per_unit"] == 105
    assert items["Banana"]["unit"] == "medium banana"
    assert items["Apple"]["calories_per_unit"] == 95

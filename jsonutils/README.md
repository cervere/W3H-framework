# JSON Assignments

## Unique ID

Read the file `data.json`.
1) Verify if the file content forms a valid JSONObject, with the key `data`.
2) Verify if the `value` of the key `data` in the JSONObject forms a valid JSONArray.  
3) Each JSONObject in the JSONArray will contain 3 keys : id, name, type. The task is to find out if there are duplicates ids. That is, if there are multiple objects in the array with the same `id`.
4) Upon finding a duplicate, print to the console, all the JSONObjects that have same id. Like the following...

```
ID: AZ1
{
  "name" : "Apple Zebra",
  "id" : "AZ1",
  "type" : "random"
}
{
  "name" : "Apricot Zenga",
  "id" : "AZ1",
  "type" : "random"
}
```

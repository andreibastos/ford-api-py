// Requisições de Usuário

var host_api = 'http://127.0.0.1:5000';

// Criar Usuário
var request = require("request");
var options = { method: 'POST',
  url: host_api+'/api/user',
  headers: 
   { 'Cache-Control': 'no-cache',     
     'Content-Type': 'application/json' },
  body: 
   { email: 'biancagonçalves@outlook.com',
     password: 'bianca',
     first_name: 'Bianca',
     last_name: 'Gonçalves' },
  json: true };

request(options, function (error, response, body) {
  if (error) throw new Error(error);

  console.log(body);
});

// Atualizar Usuário
var request = require("request");
var id_user = "id_user";
var username =  "biancagonçalves@outlook.com";
var password = 'bianca';

var options = { method: 'PUT',
  url: host_api+'/api/user/'+ id_user,
  headers: 
   { 'Cache-Control': 'no-cache',
     'Content-Type': 'application/json',
     'Authorization': "basic " +  btoa(username+":"+password)
      },
  body: 
   { email: 'biancagonçalves@outlook.com',
     password: 'bianca',
     first_name: 'Bianca 1',
     last_name: 'Gonçalves' },
  json: true };

request(options, function (error, response, body) {
  if (error) throw new Error(error);

  console.log(body);
});


// Deletar Usuário
var request = require("request");
var id_user = "id_user";
var username =  "biancagonçalves@outlook.com";
var password = 'bianca';
var options = { method: 'DELETE',
  url: host_api+'/api/user/'+id_user,
  headers: 
   { 'Cache-Control': 'no-cache', 'Authorization': "basic " +  btoa(username+":"+password) } };

request(options, function (error, response, body) {
  if (error) throw new Error(error);

  console.log(body);
});

// Pegar Usuário
var request = require("request");
var id_user = "id_user";
var options = { method: 'GET',
  url: host_api+'/api/user/'+id_user,
  headers: 
   { 'Cache-Control': 'no-cache', 'Authorization': "basic " +  btoa(username+":"+password) } };

request(options, function (error, response, body) {
  if (error) throw new Error(error);

  console.log(body);
});

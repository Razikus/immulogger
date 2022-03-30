package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"log"
	"net/http"
	"net/url"
	"os"
	"strconv"
	"time"
)

type TokenResponse struct {
	AccessToken string `json:"access_token"`
}

func getAuthorizationToken(target string, username string, password string) TokenResponse {
	resp, err := http.PostForm(target, url.Values{
		"username": {username},
		"password": {password},
		"scope":    {"SEND_LOGS"},
	})
	if err != nil {
		log.Println("Something goes wrong with auth")
	}
	body, _ := ioutil.ReadAll(resp.Body)
	var result TokenResponse
	if err := json.Unmarshal(body, &result); err != nil { // Parse []byte to go struct pointer
		fmt.Println("Can not unmarshal JSON")
	}
	return result
}

func logGenerate(target string, tokenResponse *TokenResponse, id int, fixedWait int, finishedBus chan int) {
	var jsonData = []byte(`{
		"logContent": "morpheus"
	}`)
	req, err := http.NewRequest("PUT", target, bytes.NewBuffer(jsonData))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer "+tokenResponse.AccessToken)
	if err != nil {
		log.Println("Something goes wrong with", id)
	}

	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil || resp == nil {
		log.Println("Something goes wrong with", id)
	}
	body, _ := ioutil.ReadAll(resp.Body)
	log.Println(id, "ANSWER", string(body))
	time.Sleep(time.Duration(fixedWait) * time.Millisecond)
	finishedBus <- id
}

func main() {
	host := os.Getenv("HOST")
	port := os.Getenv("PORT")
	workers, _ := strconv.Atoi(os.Getenv("WORKERS"))
	fixedWait, _ := strconv.Atoi(os.Getenv("FIXEDWAIT"))
	start := time.Now()
	token := getAuthorizationToken("http://"+host+":"+port+"/api/v1/auth/token", "admin", "admin")
	finishedBus := make(chan int)
	target := "http://" + host + ":" + port + "/api/v1/log/create"
	for i := 0; i < workers; i++ {
		fmt.Println("Spawning spawner", i)
		go logGenerate(target, &token, i, fixedWait, finishedBus)
	}
	for true {
		idFrom := <-finishedBus
		fmt.Println("SPAWNING", idFrom, "AGAIN")
		now := time.Now()
		elapsed := now.Sub(start)
		if elapsed.Minutes() > 10 {
			fmt.Println("REFRESHING TOKEN")
			token = getAuthorizationToken("http://"+host+":"+port+"/api/v1/auth/token", "admin", "admin")
			start = now
		}
		go logGenerate(target, &token, idFrom, fixedWait, finishedBus)
	}
}

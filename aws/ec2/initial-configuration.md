## EC2 Common initial configuration

```bash
sudo yum update -y
sudo yum install -y docker
sudo yum install git -y
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -a -G docker ec2-user
```

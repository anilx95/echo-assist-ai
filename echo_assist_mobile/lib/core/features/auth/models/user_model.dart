class UserModel {
  final String accessToken;
  final String refreshToken;
  final String tokenType;

  UserModel({
    required this.accessToken,
    required this.refreshToken,
    required this.tokenType,
  });

  factory UserModel.fromJson(Map<String, dynamic> json) {
    return UserModel(
      accessToken: json["access_token"],
      refreshToken: json["refresh_token"],
      tokenType: json["token_type"],
    );
  }
}
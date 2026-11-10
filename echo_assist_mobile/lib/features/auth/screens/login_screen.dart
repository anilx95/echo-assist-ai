import 'package:flutter/material.dart';

import '../../../core/routes/route_names.dart';
import '../../../core/theme/app_colors.dart';
import '../controllers/login_controller.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final TextEditingController _emailController =
      TextEditingController();

  final TextEditingController _passwordController =
      TextEditingController();

  final LoginController _controller =
      LoginController();

  bool _loading = false;
  bool _obscure = true;

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Column(
            children: [
              const SizedBox(height: 60),

              const Icon(
                Icons.visibility,
                size: 90,
                color: AppColors.primary,
              ),

              const SizedBox(height: 20),

              const Text(
                "Echo Assist AI",
                style: TextStyle(
                  fontSize: 30,
                  fontWeight: FontWeight.bold,
                ),
              ),

              const SizedBox(height: 10),

              const Text(
                "AI Powered Smart Navigation",
              ),

              const SizedBox(height: 50),

              TextField(
                controller: _emailController,
                keyboardType: TextInputType.emailAddress,
                decoration: const InputDecoration(
                  labelText: "Email",
                  prefixIcon: Icon(Icons.email),
                ),
              ),

              const SizedBox(height: 20),

              TextField(
                controller: _passwordController,
                obscureText: _obscure,
                decoration: InputDecoration(
                  labelText: "Password",
                  prefixIcon: const Icon(Icons.lock),
                  suffixIcon: IconButton(
                    icon: Icon(
                      _obscure
                          ? Icons.visibility
                          : Icons.visibility_off,
                    ),
                    onPressed: () {
                      setState(() {
                        _obscure = !_obscure;
                      });
                    },
                  ),
                ),
              ),

              const SizedBox(height: 10),

              Align(
                alignment: Alignment.centerRight,
                child: TextButton(
                  onPressed: () {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(
                        content: Text(
                          "Forgot Password will be available soon.",
                        ),
                      ),
                    );
                  },
                  child: const Text(
                    "Forgot Password?",
                  ),
                ),
              ),

              const SizedBox(height: 15),

              SizedBox(
                width: double.infinity,
                height: 55,
                child: ElevatedButton(
                  onPressed: _loading
                      ? null
                      : () async {
                          if (_emailController.text
                                  .trim()
                                  .isEmpty ||
                              _passwordController
                                  .text
                                  .isEmpty) {
                            ScaffoldMessenger.of(context)
                                .showSnackBar(
                              const SnackBar(
                                content: Text(
                                  "Please enter email and password.",
                                ),
                              ),
                            );
                            return;
                          }

                          setState(() {
                            _loading = true;
                          });

                          await _controller.login(
                            context: context,
                            email: _emailController.text.trim(),
                            password: _passwordController.text,
                          );

                          if (!mounted) return;

                          setState(() {
                            _loading = false;
                          });
                        },
                  child: _loading
                      ? const SizedBox(
                          width: 22,
                          height: 22,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            color: Colors.white,
                          ),
                        )
                      : const Text(
                          "SIGN IN",
                        ),
                ),
              ),

              const SizedBox(height: 25),

              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Text(
                    "Don't have an account?",
                  ),
                  TextButton(
                    onPressed: () {
                      Navigator.pushNamed(
                        context,
                        RouteNames.register,
                      );
                    },
                    child: const Text(
                      "Create Account",
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
import os
import streamlit as st
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_password() -> bool:
    """
    Manages user authentication. Renders a premium, secure login interface and returns 
    True if the user is authenticated, otherwise False.
    """
    def password_entered():
        """Validates the input credentials against configuration settings."""
        input_username = st.session_state.get("username_input", "")
        input_password = st.session_state.get("password_input", "")
        
        # Get credentials from st.secrets, then .env, then fall back to default values if not defined
        env_username = st.secrets.get("APP_LOGIN", os.getenv("APP_LOGIN", "doctor"))
        env_password = st.secrets.get("APP_PASSWORD", os.getenv("APP_PASSWORD", "medicalpass"))
        
        if input_username == env_username and input_password == env_password:
            st.session_state["password_correct"] = True
            # Securely clear input variables from session state
            if "password_input" in st.session_state:
                del st.session_state["password_input"]
            if "username_input" in st.session_state:
                del st.session_state["username_input"]
            if "login_error" in st.session_state:
                st.session_state["login_error"] = ""
        else:
            st.session_state["password_correct"] = False
            st.session_state["login_error"] = "Usuário ou senha inválidos. Tente novamente."

    # Initialize authentication status in session state
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    # If already authenticated, return True
    if st.session_state["password_correct"]:
        return True

    # Injecting modern typography (Outfit/Inter) and custom glassmorphism styling
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');
        
        /* Apply font family */
        html, body, [class*="css"] {
            font-family: 'Plus Jakarta Sans', 'Outfit', sans-serif;
        }

        /* Centered fading container for login card */
        .login-card {
            background: #ffffff;
            border: 1px solid #E2E8F0;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 40px -15px rgba(0, 0, 0, 0.05);
            max-width: 450px;
            margin: 60px auto;
            text-align: center;
            animation: cardFadeIn 0.8s cubic-bezier(0.16, 1, 0.3, 1);
        }

        /* Subtle logo mark */
        .brand-icon {
            display: inline-flex;
            justify-content: center;
            align-items: center;
            width: 60px;
            height: 60px;
            border-radius: 16px;
            background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%);
            color: white;
            font-size: 28px;
            margin-bottom: 20px;
            box-shadow: 0 10px 20px -5px rgba(37, 99, 235, 0.3);
        }

        .login-title {
            color: #0F172A;
            font-size: 26px;
            font-weight: 700;
            margin-bottom: 8px;
            letter-spacing: -0.5px;
        }

        .login-subtitle {
            color: #64748B;
            font-size: 14px;
            margin-bottom: 30px;
            font-weight: 400;
        }

        /* Keyframes for soft fade in transition */
        @keyframes cardFadeIn {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        /* Modern styling for the default Streamlit button inside form */
        div[data-testid="stForm"] {
            border: none !important;
            padding: 0 !important;
            background: transparent !important;
            box-shadow: none !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    
    # Grid layout to center the login container
    _, col_center, _ = st.columns([0.5, 2, 0.5])
    
    with col_center:
        st.markdown(
            """
            <div class="login-card">
                <div class="brand-icon">🩺</div>
                <div class="login-title">MedScribe</div>
                <div class="login-subtitle">Transcritor Inteligente de Consultas Médicas</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Standard input forms wrapping
        with st.form("login_form_container", clear_on_submit=False):
            st.text_input("Usuário de Acesso", key="username_input", placeholder="ex: dr.usuario")
            st.text_input("Senha", type="password", key="password_input", placeholder="••••••••")
            
            submit = st.form_submit_button("Acessar Portal Clínico", use_container_width=True)
            if submit:
                password_entered()
                st.rerun()

        # Display errors if authentication failed
        if "login_error" in st.session_state and st.session_state["login_error"]:
            st.error(st.session_state["login_error"])
            
    return False

def logout():
    """Clears authentication state and logs out the user."""
    st.session_state["password_correct"] = False
    if "login_error" in st.session_state:
        st.session_state["login_error"] = ""
    st.rerun()

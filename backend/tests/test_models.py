import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import (
    Base, User, Account, DeletionTask, AuditLog, LLMInteraction, 
    SiteMetadata, UserSettings, AccountStatus, DeletionMethod, 
    TaskStatus, LLMProvider, LLMTaskType
)


class TestModels:
    """Test database models"""
    
    @pytest.fixture
    def session(self):
        """Create test database session"""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        return Session()
    
    def test_account_model(self, session):
        """Test Account model"""
        account = Account(
            user_id=1,
            site_name="Test Site",
            site_url="https://test.com",
            username="testuser",
            encrypted_password="encrypted_password",
            email="test@example.com",
            status=AccountStatus.DISCOVERED
        )
        
        session.add(account)
        session.commit()
        
        # Test retrieval
        retrieved = session.query(Account).first()
        assert retrieved.site_name == "Test Site"
        assert retrieved.site_url == "https://test.com"
        assert retrieved.username == "testuser"
        assert retrieved.status == AccountStatus.DISCOVERED
        assert retrieved.created_at is not None
        assert retrieved.updated_at is not None
    
    def test_deletion_task_model(self, session):
        """Test DeletionTask model"""
        # Create account first
        account = Account(
            user_id=1,
            site_name="Test Site",
            site_url="https://test.com",
            username="testuser",
            encrypted_password="encrypted_password",
            status=AccountStatus.DISCOVERED
        )
        session.add(account)
        session.commit()
        
        # Create deletion task
        task = DeletionTask(
            account_id=account.id,
            method=DeletionMethod.AUTOMATED,
            status=TaskStatus.PENDING,
            attempts=0,
            deletion_url="https://test.com/delete"
        )
        
        session.add(task)
        session.commit()
        
        # Test retrieval
        retrieved = session.query(DeletionTask).first()
        assert retrieved.account_id == account.id
        assert retrieved.method == DeletionMethod.AUTOMATED
        assert retrieved.status == TaskStatus.PENDING
        assert retrieved.attempts == 0
        assert retrieved.created_at is not None
        
        # Test relationship
        assert retrieved.account.site_name == "Test Site"
    
    def test_audit_log_model(self, session):
        """Test AuditLog model"""
        # Create account first
        account = Account(
            user_id=1,
            site_name="Test Site",
            site_url="https://test.com",
            username="testuser",
            encrypted_password="encrypted_password",
            status=AccountStatus.DISCOVERED
        )
        session.add(account)
        session.commit()
        
        # Create audit log
        log = AuditLog(
            user_id=1,
            account_id=account.id,
            action="test_action",
            details={"test": "data"},
            masked_credentials=True,
            user_agent="test_agent",
            ip_address="127.0.0.1"
        )
        
        session.add(log)
        session.commit()
        
        # Test retrieval
        retrieved = session.query(AuditLog).first()
        assert retrieved.account_id == account.id
        assert retrieved.action == "test_action"
        assert retrieved.details == {"test": "data"}
        assert retrieved.masked_credentials is True
        assert retrieved.user_agent == "test_agent"
        assert retrieved.ip_address == "127.0.0.1"
        assert retrieved.created_at is not None
        
        # Test relationship
        assert retrieved.account.site_name == "Test Site"
    
    def test_llm_interaction_model(self, session):
        """Test LLMInteraction model"""
        # Create account first
        account = Account(
            user_id=1,
            site_name="Test Site",
            site_url="https://test.com",
            username="testuser",
            encrypted_password="encrypted_password",
            status=AccountStatus.DISCOVERED
        )
        session.add(account)
        session.commit()
        
        # Create LLM interaction
        interaction = LLMInteraction(
            account_id=account.id,
            provider=LLMProvider.OPENAI,
            task_type=LLMTaskType.DISCOVERY,
            prompt="Test prompt",
            response="Test response",
            tokens_used=100,
            cost=0.002
        )
        
        session.add(interaction)
        session.commit()
        
        # Test retrieval
        retrieved = session.query(LLMInteraction).first()
        assert retrieved.account_id == account.id
        assert retrieved.provider == LLMProvider.OPENAI
        assert retrieved.task_type == LLMTaskType.DISCOVERY
        assert retrieved.prompt == "Test prompt"
        assert retrieved.response == "Test response"
        assert retrieved.tokens_used == 100
        assert float(retrieved.cost) == 0.002
        assert retrieved.created_at is not None
        
        # Test relationship
        assert retrieved.account.site_name == "Test Site"
    
    def test_site_metadata_model(self, session):
        """Test SiteMetadata model"""
        metadata = SiteMetadata(
            site_name="Test Site",
            site_url="https://test.com",
            deletion_url="https://test.com/delete",
            privacy_email="privacy@test.com",
            deletion_instructions="Go to settings and delete",
            automation_difficulty=5,
            success_rate=0.85,
            login_selectors={"username": "#username", "password": "#password"},
            deletion_selectors={"delete_button": "#delete-account"},
            confirmation_texts=["Are you sure?", "This will delete your account"]
        )
        
        session.add(metadata)
        session.commit()
        
        # Test retrieval
        retrieved = session.query(SiteMetadata).first()
        assert retrieved.site_name == "Test Site"
        assert retrieved.site_url == "https://test.com"
        assert retrieved.deletion_url == "https://test.com/delete"
        assert retrieved.privacy_email == "privacy@test.com"
        assert retrieved.deletion_instructions == "Go to settings and delete"
        assert retrieved.automation_difficulty == 5
        assert float(retrieved.success_rate) == 0.85
        assert retrieved.login_selectors == {"username": "#username", "password": "#password"}
        assert retrieved.deletion_selectors == {"delete_button": "#delete-account"}
        assert retrieved.confirmation_texts == ["Are you sure?", "This will delete your account"]
        assert retrieved.last_updated is not None
    
    def test_user_settings_model(self, session):
        """Test UserSettings model"""
        settings = UserSettings(
            user_id="test_user",
            email="test@gmail.com",
            email_password="encrypted_password",
            name="Test User",
            auto_confirm_deletions=False,
            email_notifications=True,
            max_cost_per_deletion=5.00
        )
        
        session.add(settings)
        session.commit()
        
        # Test retrieval
        retrieved = session.query(UserSettings).first()
        assert retrieved.user_id == "test_user"
        assert retrieved.email == "test@gmail.com"
        assert retrieved.email_password == "encrypted_password"
        assert retrieved.name == "Test User"
        assert retrieved.auto_confirm_deletions is False
        assert retrieved.email_notifications is True
        assert retrieved.max_cost_per_deletion == 5.00
        assert retrieved.created_at is not None
        assert retrieved.updated_at is not None
    
    def test_account_status_enum(self):
        """Test AccountStatus enum"""
        assert AccountStatus.DISCOVERED.value == "discovered"
        assert AccountStatus.PENDING.value == "pending"
        assert AccountStatus.IN_PROGRESS.value == "in_progress"
        assert AccountStatus.COMPLETED.value == "completed"
        assert AccountStatus.FAILED.value == "failed"
    
    def test_deletion_method_enum(self):
        """Test DeletionMethod enum"""
        assert DeletionMethod.AUTOMATED.value == "automated"
        assert DeletionMethod.EMAIL.value == "email"
    
    def test_task_status_enum(self):
        """Test TaskStatus enum"""
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.IN_PROGRESS.value == "in_progress"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"
    
    def test_llm_provider_enum(self):
        """Test LLMProvider enum"""
        assert LLMProvider.OPENAI.value == "openai"
        assert LLMProvider.ANTHROPIC.value == "anthropic"
    
    def test_llm_task_type_enum(self):
        """Test LLMTaskType enum"""
        assert LLMTaskType.DISCOVERY.value == "discovery"
        assert LLMTaskType.NAVIGATION.value == "navigation"
        assert LLMTaskType.EMAIL_GENERATION.value == "email_generation"
    
    def test_relationships(self, session):
        """Test model relationships"""
        # Create account
        account = Account(
            user_id=1,
            site_name="Test Site",
            site_url="https://test.com",
            username="testuser",
            encrypted_password="encrypted_password",
            status=AccountStatus.DISCOVERED
        )
        session.add(account)
        session.commit()
        
        # Create related records
        deletion_task = DeletionTask(
            account_id=account.id,
            method=DeletionMethod.AUTOMATED,
            status=TaskStatus.PENDING
        )
        
        audit_log = AuditLog(
            account_id=account.id,
            action="test_action",
            details={"test": "data"},
            masked_credentials=True
        )
        
        llm_interaction = LLMInteraction(
            account_id=account.id,
            provider=LLMProvider.OPENAI,
            task_type=LLMTaskType.DISCOVERY,
            prompt="Test prompt",
            response="Test response",
            tokens_used=100,
            cost=0.002
        )
        
        session.add_all([deletion_task, audit_log, llm_interaction])
        session.commit()
        
        # Test relationships
        retrieved_account = session.query(Account).first()
        assert len(retrieved_account.deletion_tasks) == 1
        assert len(retrieved_account.audit_logs) == 1
        assert len(retrieved_account.llm_interactions) == 1
        
        assert retrieved_account.deletion_tasks[0].method == DeletionMethod.AUTOMATED
        assert retrieved_account.audit_logs[0].action == "test_action"
        assert retrieved_account.llm_interactions[0].provider == LLMProvider.OPENAI
        
        # Test back references
        assert retrieved_account.deletion_tasks[0].account == retrieved_account
        assert retrieved_account.audit_logs[0].account == retrieved_account
        assert retrieved_account.llm_interactions[0].account == retrieved_account